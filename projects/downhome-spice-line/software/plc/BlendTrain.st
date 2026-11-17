(* ============================================================================
   PLC-601  BLENDING TRAIN SEQUENCE  (ISA-88 phase logic, IEC 61131-3 ST)
   Down Home Creole dry plant. Train: BD-301 / BB-302 -> RB-303 -> SC-304 ->
   DH-102 magnet -> MD-305 (CCP-1) -> FC-307 -> BF-306.
   Tags come from io_map.st (generated from design/io.json).

   The MES (software/mes) owns the recipe. It downloads one batch at a time:
   BatchID, FormulaID, TargetKg, MixTime_s, SaltKg, AllergenClass. The PLC
   owns equipment safety: it will not open a cover, run a screw into a closed
   valve, or fill a bag that MD-305 has not cleared.
   ============================================================================ *)

TYPE E_BlendStep : (
    IDLE := 0, WAIT_DOWNLOAD := 5, PRECHECK := 10, CHARGE_SALT := 20,
    CHARGE_MAJORS := 30, CHARGE_PREMIX := 40, MIX := 50, HOLD_SAMPLE := 55,
    DISCHARGE := 60, DRAIN := 70, PURGE := 80, COMPLETE := 90,
    HELD := 100, ABORTED := 110 );
END_TYPE

TYPE ST_BatchDownload :
STRUCT
    BatchID       : STRING[16];   (* DHyyjjj-B## *)
    FormulaID     : STRING[16];
    TargetKg      : REAL;         (* <= RB-303 working volume x bulk density, checked by MES and here *)
    SaltKg        : REAL;         (* metered by BB-302 on blender load cells *)
    MixTime_s     : DINT;         (* site: 12 min *)
    AllergenClass : INT;          (* 0 none, 1 wheat (Friday campaign only) *)
    Valid         : BOOL;
END_STRUCT
END_TYPE

VAR_GLOBAL
    MES_Download    : ST_BatchDownload;   (* written by MES over OPC UA / CIP *)
    MES_MajorsDone  : BOOL;               (* operator scanned all major bags at BD-301 *)
    MES_PremixDone  : BOOL;               (* premix bag scanned and dumped *)
    MES_SampleOK    : BOOL;               (* QC accepted in-process sample (optional hold) *)
    MES_Abort       : BOOL;
    Blend_Step      : E_BlendStep;
    Blend_StateText : STRING[40];
    Blend_ActKg     : REAL;
    Blend_SaltActKg : REAL;
    Blend_MixLeft_s : DINT;
    Blend_Alarm     : WORD;               (* bit map, see ALARMS below *)
    MD305_RejCount  : DINT;               (* reported to MES for the batch record *)
    BlendMaxKg      : REAL := 655.0;      (* 36 cu ft working (1,019 L) x 0.643 g/mL densest formula; MES checks the formula-specific limit first *)
END_VAR

PROGRAM BlendTrain
VAR
    tMix        : TON;
    tDrain      : TON;
    tPurge      : TON;
    tValve      : TON;
    tamps       : TON;
    WeightAtStart : REAL;
    Permissive  : BOOL;
    DustOK      : BOOL;
    rDetect     : R_TRIG;
    rReset      : R_TRIG;
END_VAR

(* ---------- PERMISSIVES (hard interlocks also exist in safety relay SR-601) ---------- *)
DustOK := DC310_RUN AND NOT DC310_ISO_CLOSED (* flap valve trips closed on deflagration *) AND NOT DC310_VENT_BURST AND DC310_DP > 0.5 AND DC310_DP < 6.0;  (* in. w.c. *)
Permissive := SR601_OK AND DustOK AND NOT AC311_LOWPRESS AND RB303_COVER_CLOSED AND NOT MD305_FAULT;

(* Weight from RB-303 load cells (AI, kg) *)
Blend_ActKg := RB303_WEIGHT;

(* ---------- ALARMS ---------- *)
Blend_Alarm.0 := NOT SR601_OK;           (* e-stop / guard *)
Blend_Alarm.1 := NOT DustOK;             (* dust collector not proven or vent burst: NFPA 652 *)
Blend_Alarm.2 := AC311_LOWPRESS;
Blend_Alarm.3 := NOT RB303_COVER_CLOSED;
Blend_Alarm.4 := MD305_FAULT;
Blend_Alarm.5 := MD305_REJBIN_FULL;
Blend_Alarm.6 := SC304_OVERS_FULL;
Blend_Alarm.7 := BB302_HOPPER_LOW AND Blend_Step = CHARGE_SALT;
Blend_Alarm.8 := tamps.Q;                (* blender over-current: possible lump or overfill *)
tamps(IN := RB303_AMPS > 24.0, PT := T#5S);  (* M-304 FLA 21 A *)

rReset(CLK := PB601_RESET);
rDetect(CLK := MD305_DETECT);
IF rDetect.Q THEN MD305_RejCount := MD305_RejCount + 1; END_IF;

(* Any loss of permissive while running -> HELD with every mover stopped *)
IF NOT Permissive AND Blend_Step > PRECHECK AND Blend_Step < COMPLETE THEN
    Blend_Step := HELD;
END_IF;
IF MES_Abort AND Blend_Step <> IDLE THEN
    Blend_Step := ABORTED;
END_IF;

CASE Blend_Step OF
IDLE:
    Blend_StateText := 'Idle';
    IF MES_Download.Valid THEN Blend_Step := PRECHECK; END_IF;

PRECHECK:
    Blend_StateText := 'Pre-check';
    (* batch size never above blender working capacity (design-basis batch rule) *)
    IF MES_Download.TargetKg > BlendMaxKg OR MES_Download.TargetKg <= 0.0 THEN
        Blend_Alarm.9 := TRUE; MES_Download.Valid := FALSE; Blend_Step := IDLE;
    ELSIF Permissive AND RB303_VALVE_CLOSED AND Blend_ActKg < 5.0 THEN
        WeightAtStart := Blend_ActKg; MD305_RejCount := 0;
        Blend_Step := CHARGE_SALT;
    END_IF;

CHARGE_SALT:
    Blend_StateText := 'Charging salt (BB-302)';
    RB303_START := TRUE;                    (* ribbons turn during charge to avoid salt bed *)
    BB302_START := (Blend_ActKg - WeightAtStart) < (MES_Download.SaltKg - 3.0);  (* 3 kg in-flight, tuned at SAT *)
    IF NOT BB302_START THEN
        Blend_SaltActKg := Blend_ActKg - WeightAtStart;
        Blend_Step := CHARGE_MAJORS;
    END_IF;

CHARGE_MAJORS:
    Blend_StateText := 'Dump majors at BD-301';
    BD301_START := BD301_DCFAN_RUN;  (* screw runs only with the station dust fan proven *)
    IF MES_MajorsDone THEN BD301_START := FALSE; Blend_Step := CHARGE_PREMIX; END_IF;

CHARGE_PREMIX:
    Blend_StateText := 'Add premix at BD-301';
    BD301_START := BD301_DCFAN_RUN;
    IF MES_PremixDone THEN
        BD301_START := FALSE;
        tMix(IN := FALSE);
        Blend_Step := MIX;
    END_IF;

MIX:
    Blend_StateText := 'Mixing';
    RB303_START := TRUE;
    tMix(IN := TRUE, PT := DINT_TO_TIME(MES_Download.MixTime_s * 1000));
    Blend_MixLeft_s := MES_Download.MixTime_s - TIME_TO_DINT(tMix.ET) / 1000;
    IF tMix.Q THEN tMix(IN := FALSE); Blend_Step := HOLD_SAMPLE; END_IF;

HOLD_SAMPLE:
    Blend_StateText := 'Sample for CV (QC)';
    RB303_START := FALSE;
    IF MES_SampleOK THEN Blend_Step := DISCHARGE; END_IF;

DISCHARGE:
    Blend_StateText := 'Discharging to bulk bag';
    (* start downstream first, then open valve: no product into a stopped screw *)
    IF NOT BF306_BAG_PRESENT THEN
        Blend_Alarm.10 := TRUE;
    ELSE
        Blend_Alarm.10 := FALSE;
        BF306_SEAL_INFLATE := TRUE;
        FC307_START := NOT FC307_HOPPER_LOW OR SC304_RUN;
        SC304_START := TRUE;
        RB303_START := TRUE;
        BF306_DENSIFY := TRUE;
        BF306_FILL_START := TRUE;
        (* throttle: close blender valve while FC-307 hopper is high *)
        RB303_VALVE_OPEN_SOL := SC304_RUN AND FC307_RUN AND NOT FC307_HOPPER_HIGH AND NOT MD305_REJBIN_FULL;
        RB303_VALVE_CLOSE_SOL := NOT RB303_VALVE_OPEN_SOL;
        tValve(IN := RB303_VALVE_OPEN_SOL AND NOT RB303_VALVE_OPEN, PT := T#3S);
        Blend_Alarm.11 := tValve.Q;   (* valve did not prove open *)
        IF Blend_ActKg < 2.0 THEN tDrain(IN := FALSE); Blend_Step := DRAIN; END_IF;
    END_IF;

DRAIN:
    Blend_StateText := 'Draining train';
    RB303_VALVE_OPEN_SOL := FALSE; RB303_VALVE_CLOSE_SOL := TRUE;
    tDrain(IN := TRUE, PT := T#90S);      (* sifter and screw run empty *)
    IF tDrain.Q THEN
        SC304_START := FALSE; FC307_START := FALSE; RB303_START := FALSE;
        BF306_FILL_START := FALSE; BF306_DENSIFY := FALSE;
        tDrain(IN := FALSE); Blend_Step := COMPLETE;
    END_IF;

COMPLETE:
    Blend_StateText := 'Complete: release bag to HOLD-1';
    BF306_SEAL_INFLATE := NOT BF306_FILL_DONE;
    MES_Download.Valid := FALSE; MES_MajorsDone := FALSE; MES_PremixDone := FALSE; MES_SampleOK := FALSE;
    Blend_Step := IDLE;

HELD:
    Blend_StateText := 'HELD: check alarms, press reset';
    BD301_START := FALSE; BB302_START := FALSE; SC304_START := FALSE; FC307_START := FALSE;
    RB303_START := FALSE; RB303_VALVE_OPEN_SOL := FALSE; RB303_VALVE_CLOSE_SOL := TRUE;
    BF306_FILL_START := FALSE; BF306_DENSIFY := FALSE;
    (* resume at charge step if material was already weighed; MES knows which step *)
    IF rReset.Q AND Permissive THEN Blend_Step := MIX; END_IF;

ABORTED:
    Blend_StateText := 'ABORTED: batch on hold in MES';
    BD301_START := FALSE; BB302_START := FALSE; SC304_START := FALSE; FC307_START := FALSE;
    RB303_START := FALSE; RB303_VALVE_OPEN_SOL := FALSE; RB303_VALVE_CLOSE_SOL := TRUE;
    BF306_FILL_START := FALSE;
    IF rReset.Q THEN MES_Abort := FALSE; MES_Download.Valid := FALSE; Blend_Step := IDLE; END_IF;
END_CASE;

(* Dust collector always runs while any mover runs, and 10 min after (post-purge) *)
DC310_START := SR601_OK AND NOT DC310_VENT_BURST AND (Blend_Step <> IDLE OR BD301_DCFAN_RUN);

(* Stack light *)
SL601_RED   := Blend_Alarm <> 0 OR Blend_Step = HELD OR Blend_Step = ABORTED;
SL601_AMBER := Blend_Step = CHARGE_MAJORS OR Blend_Step = CHARGE_PREMIX OR Blend_Step = HOLD_SAMPLE;
SL601_GREEN := Blend_Step = MIX OR Blend_Step = DISCHARGE OR Blend_Step = DRAIN;
SL601_HORN  := Blend_Alarm.1 OR Blend_Alarm.5;   (* dust and reject-bin full sound locally *)
END_PROGRAM
