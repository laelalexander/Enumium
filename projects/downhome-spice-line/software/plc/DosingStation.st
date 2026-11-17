(* ============================================================================
   P1-225  PHASE 1 DOSING STATION  (IEC 61131-3 ST, CODESYS 3.5 on WAGO PFC200 750-8212)
   Down Home Creole Phase 1 prototype. Ring of up to 12 ingredient bins
   (P1-211) with 2 in volumetric screw feeders (P1-212, VFD P1-226) dosing
   one at a time into weigh hopper P1-220 (3 x 50 kg cells, Rice Lake 880
   indicator P1-222, 10 g division). When the list is done, butterfly valve
   P1-223 opens and flexible screw P1-224 carries the charge to blender P1-301
   (on riser stand P1-311). The hand-weighed lines and the premix are then
   tipped into the screw's intake grate, so nobody lifts a pail above waist height.

   The MES owns the recipe and the lot genealogy:
     GET /api/batch/<id>/doselist  -> MES_DoseList (largest dose first)
     POST /api/dose {batch, bin, actual_kg} after each finished dose.
   The PLC owns the equipment: one feeder at a time, never a screw into a
   closed valve or a full blender, no dose from a bin at low level.

   Dosing method (gain in weight, per bin):
     FAST  : VFD at FastHz until  net >= target - SlowBand - InFlight
     SLOW  : VFD at SlowHz until  net >= target - InFlight
     SETTLE: feeder off, wait SettleT, read stable weight
     CHECK : |actual - target| <= TolKg  -> report;  under -> one JOG pulse
             (max 3) ;  over -> OVERDOSE alarm, hold for the operator.
   In-flight (material still falling after the screw stops) is learned per
   bin: InFlight := InFlight + 0.5 * (actual - target), clamped 0..0.5 kg.
   No-flow: hopper gain < 0.05 kg in NoFlowT while the feeder runs -> alarm
   (bridged bin, empty bin, broken shear pin).
   Timers and speeds marked (SAT) are tuned at site acceptance.
   E-stop and the hopper/screw guards are hard-wired through safety relay
   SR-P1 and remove VFD enable; this code only sees the healthy bit.
   ============================================================================ *)

TYPE E_DoseStep : (
    IDLE := 0, WAIT_LIST := 5, PRECHECK := 10, TARE := 20, FAST := 30, SLOW := 40,
    SETTLE := 50, CHECK := 60, JOG := 65, REPORT := 70, NEXT := 80,
    TRANSFER := 90, TRANSFER_DRAIN := 95, COMPLETE := 100, HELD := 110, ABORTED := 120 );
END_TYPE

TYPE ST_DoseStep :
STRUCT
    Bin        : INT;          (* 1..12, ring position *)
    Ingredient : STRING[24];
    TargetKg   : REAL;         (* >= 4 kg by MES rule *)
    TolKg      : REAL;         (* max(1 % of target, 0.02 kg) *)
END_STRUCT
END_TYPE

TYPE ST_DoseList :
STRUCT
    BatchID  : STRING[16];
    FormulaID: STRING[16];
    Steps    : ARRAY[1..12] OF ST_DoseStep;
    Count    : INT;
    Valid    : BOOL;
END_STRUCT
END_TYPE

TYPE ST_DoseResult :
STRUCT
    BatchID  : STRING[16];
    Bin      : INT;
    ActualKg : REAL;
    Ready    : BOOL;           (* MES gateway posts /api/dose then sets Ack *)
    Ack      : BOOL;
END_STRUCT
END_TYPE

VAR_GLOBAL CONSTANT
    NBINS        : INT  := 12;
    HOPPER_MAXKG : REAL := 100.0;   (* 3 x 50 kg cells, 2/3 derated for the hopper *)
    BLENDER_MAXKG: REAL := 95.0;    (* P1-301 6 cu ft x densest blend (0.56 g/ml) *)
END_VAR

VAR_GLOBAL
    (* ---- I/O (WAGO 750-8212 rack: 750-430 DI, 750-530 DO, 750-455 AI 4-20 mA, Modbus RTU to GS20 drives) ---- *)
    DI_SafetyOK      AT %IX0.0  : BOOL;     (* SR-P1 healthy: e-stops, hopper lid, screw guard *)
    DI_ValveClosed   AT %IX0.1  : BOOL;     (* P1-223 closed limit *)
    DI_ValveOpen     AT %IX0.2  : BOOL;     (* P1-223 open limit *)
    DI_ScrewRunning  AT %IX0.3  : BOOL;     (* P1-224 motor contactor aux *)
    DI_BlenderReady  AT %IX0.4  : BOOL;     (* P1-301 cover closed and not discharging *)
    DI_BlenderHigh   AT %IX0.5  : BOOL;     (* P1-301 high level, capacitance probe *)
    DI_DustFanOn     AT %IX0.6  : BOOL;     (* P1-310 fan running *)
    DI_BinLow        AT %IX1.0  : ARRAY[1..12] OF BOOL;   (* P1-213 Soliphant FTM20, TRUE = covered (fail-safe) *)
    DO_ValveOpen     AT %QX0.0  : BOOL;     (* P1-223 solenoid *)
    DO_ScrewRun      AT %QX0.1  : BOOL;     (* P1-224 contactor *)
    DO_Horn          AT %QX0.2  : BOOL;
    DO_Beacon        AT %QX0.3  : BOOL;
    DO_Agitator      AT %QX1.0  : ARRAY[1..12] OF BOOL;   (* bin flow aid, density < 0.5 kg/L bins only *)
    AI_HopperKg                 : REAL;     (* P1-222 Rice Lake 880 gross weight over Modbus TCP, 10 g *)
    AI_HopperStable             : BOOL;     (* 880 motion bit inverted *)
    VFD_Run          : ARRAY[1..12] OF BOOL;      (* GS20 drives, Modbus RTU *)
    VFD_Hz           : ARRAY[1..12] OF REAL;
    VFD_Fault        : ARRAY[1..12] OF BOOL;

    (* ---- MES interface (OPC UA server on the PFC200, written by the MES gateway) ---- *)
    MES_DoseList     : ST_DoseList;
    MES_Result       : ST_DoseResult;
    MES_Start        : BOOL;
    MES_HandAddsDone : BOOL;            (* hand-weighed lines, then the premix, tipped into the P1-224 intake grate *)
    MES_Abort        : BOOL;
    HMI_Resume       : BOOL;
    HMI_Reset        : BOOL;

    (* ---- status ---- *)
    Dose_Step        : E_DoseStep;
    Dose_Index       : INT;
    Dose_NetKg       : REAL;
    Dose_Alarm       : STRING[60];
    Dose_HeldFrom    : E_DoseStep;

    (* ---- per-bin parameters, retained (learned in-flight survives power loss) ---- *)
    InFlightKg       : ARRAY[1..12] OF REAL := [12(0.15)];   (* (SAT) start value *)
    FastHz           : ARRAY[1..12] OF REAL := [12(60.0)];   (* about 700 L/h at 60 Hz, 2 in screw *)
    SlowHz           : ARRAY[1..12] OF REAL := [12(12.0)];   (* (SAT) *)
    SlowBandKg       : ARRAY[1..12] OF REAL := [12(1.0)];    (* (SAT) *)
END_VAR

PROGRAM DosingStation
VAR
    tStep     : TON;
    tNoFlow   : TON;
    tSettle   : TON;
    tTransfer : TON;
    TareKg    : REAL;
    LastKg    : REAL;
    ActualKg  : REAL;
    Jogs      : INT;
    i         : INT;
    b         : INT;           (* bin of the current step *)
    s         : ST_DoseStep;
    SumKg     : REAL;
    NoFlowT   : TIME := T#8S;  (* (SAT) *)
    SettleT   : TIME := T#3S;  (* (SAT) *)
    JogT      : TIME := T#600MS;
    DrainT    : TIME := T#20S; (* screw runs on after the hopper reads empty *)
    MaxDoseT  : TIME := T#10M; (* longest planned dose < 8 min *)
END_VAR

(* ---------- always: interlocks ---------- *)
IF NOT DI_SafetyOK OR MES_Abort THEN
    FOR i := 1 TO NBINS DO VFD_Run[i] := FALSE; END_FOR
    DO_ScrewRun := FALSE;
    DO_ValveOpen := FALSE;
    IF Dose_Step <> IDLE AND Dose_Step <> COMPLETE THEN
        Dose_Alarm := SEL(MES_Abort, 'SAFETY CIRCUIT OPEN', 'ABORTED BY MES');
        Dose_Step := ABORTED;
    END_IF
END_IF

(* the transfer screw may only run with the valve open, the blender ready and the dust fan on *)
IF DO_ScrewRun AND NOT (DI_ValveOpen AND DI_BlenderReady AND DI_DustFanOn AND NOT DI_BlenderHigh) THEN
    DO_ScrewRun := FALSE;
    DO_ValveOpen := FALSE;
    Dose_Alarm := 'TRANSFER PERMISSIVE LOST';
    Dose_HeldFrom := Dose_Step;
    Dose_Step := HELD;
END_IF

(* one feeder at a time: only the current bin may run *)
FOR i := 1 TO NBINS DO
    IF VFD_Run[i] AND ((Dose_Step <> FAST AND Dose_Step <> SLOW AND Dose_Step <> JOG) OR i <> b) THEN
        VFD_Run[i] := FALSE;
    END_IF
    IF VFD_Fault[i] AND VFD_Run[i] THEN
        VFD_Run[i] := FALSE;
        Dose_Alarm := CONCAT('FEEDER FAULT BIN ', INT_TO_STRING(i));
        Dose_HeldFrom := Dose_Step;
        Dose_Step := HELD;
    END_IF
    DO_Agitator[i] := VFD_Run[i];       (* flow aid only while its feeder runs *)
END_FOR

Dose_NetKg := AI_HopperKg - TareKg;

(* ---------- sequence ---------- *)
CASE Dose_Step OF

IDLE:
    IF MES_Start THEN Dose_Step := WAIT_LIST; END_IF

WAIT_LIST:
    IF MES_DoseList.Valid AND MES_DoseList.Count >= 1 AND MES_DoseList.Count <= NBINS THEN
        SumKg := 0.0;
        FOR i := 1 TO MES_DoseList.Count DO SumKg := SumKg + MES_DoseList.Steps[i].TargetKg; END_FOR
        IF SumKg > HOPPER_MAXKG OR SumKg > BLENDER_MAXKG THEN
            Dose_Alarm := 'DOSE LIST EXCEEDS HOPPER OR BLENDER';
            Dose_Step := ABORTED;
        ELSE
            Dose_Index := 1;
            Dose_Step := PRECHECK;
        END_IF
    END_IF

PRECHECK:
    (* hopper empty, valve closed, dust fan on *)
    IF NOT DI_DustFanOn THEN
        Dose_Alarm := 'DUST COLLECTOR P1-310 OFF';
    ELSIF NOT DI_ValveClosed THEN
        Dose_Alarm := 'HOPPER VALVE NOT CLOSED';
    ELSIF AI_HopperKg > 0.5 THEN
        Dose_Alarm := 'HOPPER NOT EMPTY';
    ELSE
        Dose_Alarm := '';
        Dose_Step := TARE;
    END_IF

TARE:
    s := MES_DoseList.Steps[Dose_Index];
    b := s.Bin;
    IF b < 1 OR b > NBINS THEN
        Dose_Alarm := 'BAD BIN NUMBER IN DOSE LIST';
        Dose_Step := ABORTED;
    ELSIF NOT DI_BinLow[b] THEN
        Dose_Alarm := CONCAT('BIN LOW: REFILL BIN ', INT_TO_STRING(b));   (* MES checked book stock; this is the probe *)
        Dose_HeldFrom := TARE;
        Dose_Step := HELD;
    ELSIF AI_HopperStable THEN
        TareKg := AI_HopperKg;        (* cumulative: each dose is tared on the previous ones *)
        LastKg := AI_HopperKg;
        Jogs := 0;
        VFD_Hz[b] := FastHz[b];
        VFD_Run[b] := TRUE;
        Dose_Step := FAST;
    END_IF

FAST, SLOW:
    IF Dose_Step = FAST AND Dose_NetKg >= s.TargetKg - SlowBandKg[b] - InFlightKg[b] THEN
        VFD_Hz[b] := SlowHz[b];
        Dose_Step := SLOW;
    ELSIF Dose_NetKg >= s.TargetKg - InFlightKg[b] THEN
        VFD_Run[b] := FALSE;
        Dose_Step := SETTLE;
    END_IF
    (* no-flow: the hopper must gain 50 g in NoFlowT *)
    tNoFlow(IN := VFD_Run[b] AND (AI_HopperKg - LastKg) < 0.05, PT := NoFlowT);
    IF (AI_HopperKg - LastKg) >= 0.05 THEN LastKg := AI_HopperKg; END_IF
    IF tNoFlow.Q THEN
        VFD_Run[b] := FALSE;
        Dose_Alarm := CONCAT('NO FLOW BIN ', INT_TO_STRING(b));
        Dose_HeldFrom := SLOW;    (* resume keeps TareKg and finishes the dose at slow speed *)
        Dose_Step := HELD;
    END_IF
    tStep(IN := TRUE, PT := MaxDoseT);
    IF tStep.Q THEN
        VFD_Run[b] := FALSE;
        Dose_Alarm := CONCAT('DOSE TIMEOUT BIN ', INT_TO_STRING(b));
        Dose_HeldFrom := SETTLE;
        Dose_Step := HELD;
    END_IF

SETTLE:
    tSettle(IN := AI_HopperStable, PT := SettleT);
    IF tSettle.Q THEN
        tSettle(IN := FALSE);
        ActualKg := AI_HopperKg - TareKg;
        Dose_Step := CHECK;
    END_IF

CHECK:
    IF ABS(ActualKg - s.TargetKg) <= s.TolKg THEN
        IF Jogs = 0 THEN
            (* learn in-flight only from clean single-shot doses *)
            InFlightKg[b] := LIMIT(0.0, InFlightKg[b] + 0.5 * (ActualKg - s.TargetKg), 0.5);
        END_IF
        Dose_Step := REPORT;
    ELSIF ActualKg < s.TargetKg - s.TolKg AND Jogs < 3 THEN
        Jogs := Jogs + 1;
        VFD_Hz[b] := SlowHz[b];
        VFD_Run[b] := TRUE;
        Dose_Step := JOG;
    ELSE
        (* over-dose or still short after 3 jogs: the operator corrects by hand at the hopper
           (scoop out or hand add on the 880) and resumes; the MES rejects anything outside tolerance *)
        Dose_Alarm := SEL(ActualKg > s.TargetKg, CONCAT('UNDERDOSE BIN ', INT_TO_STRING(b)), CONCAT('OVERDOSE BIN ', INT_TO_STRING(b)));
        Dose_HeldFrom := SETTLE;
        Dose_Step := HELD;
    END_IF

JOG:
    tStep(IN := TRUE, PT := JogT);
    IF tStep.Q THEN
        VFD_Run[b] := FALSE;
        Dose_Step := SETTLE;
    END_IF

REPORT:
    MES_Result.BatchID := MES_DoseList.BatchID;
    MES_Result.Bin := b;
    MES_Result.ActualKg := ActualKg;
    MES_Result.Ready := TRUE;
    IF MES_Result.Ack THEN
        MES_Result.Ready := FALSE;
        MES_Result.Ack := FALSE;
        Dose_Step := NEXT;
    END_IF

NEXT:
    IF Dose_Index < MES_DoseList.Count THEN
        Dose_Index := Dose_Index + 1;
        Dose_Step := TARE;
    ELSIF DI_BlenderReady AND NOT DI_BlenderHigh THEN
        DO_ValveOpen := TRUE;
        Dose_Step := TRANSFER;
    END_IF

TRANSFER:
    (* the bin charge goes first; the screw keeps running for the hand adds *)
    IF DI_ValveOpen THEN DO_ScrewRun := TRUE; END_IF
    IF AI_HopperKg < 0.2 AND AI_HopperStable THEN
        DO_ValveOpen := FALSE;
        Dose_Step := TRANSFER_DRAIN;
    END_IF

TRANSFER_DRAIN:
    (* operator tips the hand-weighed pails, then the premix last, into the P1-224 intake grate and
       confirms on the MES; the screw then runs on DrainT to empty the tube into the blender *)
    IF MES_HandAddsDone THEN
        tTransfer(IN := TRUE, PT := DrainT);
        IF tTransfer.Q THEN
            tTransfer(IN := FALSE);
            DO_ScrewRun := FALSE;
            MES_HandAddsDone := FALSE;
            Dose_Step := COMPLETE;
        END_IF
    END_IF

COMPLETE:
    MES_Start := FALSE;
    MES_DoseList.Valid := FALSE;
    IF HMI_Reset THEN Dose_Step := IDLE; Dose_Alarm := ''; END_IF

HELD:
    FOR i := 1 TO NBINS DO VFD_Run[i] := FALSE; END_FOR
    DO_ScrewRun := FALSE;
    IF HMI_Resume AND DI_SafetyOK THEN
        HMI_Resume := FALSE;
        Dose_Alarm := '';
        IF Dose_HeldFrom = SETTLE THEN
            Dose_Step := SETTLE;          (* re-weigh after the operator's correction *)
        ELSIF Dose_HeldFrom = TARE THEN
            Dose_Step := TARE;
        ELSIF Dose_HeldFrom = FAST OR Dose_HeldFrom = SLOW THEN
            LastKg := AI_HopperKg;
            VFD_Hz[b] := SlowHz[b];
            VFD_Run[b] := TRUE;
            Dose_Step := SLOW;
        ELSIF Dose_HeldFrom = TRANSFER THEN
            DO_ValveOpen := TRUE;
            Dose_Step := TRANSFER;
        ELSE
            Dose_Step := Dose_HeldFrom;
        END_IF
    END_IF

ABORTED:
    FOR i := 1 TO NBINS DO VFD_Run[i] := FALSE; END_FOR
    DO_ScrewRun := FALSE;
    DO_ValveOpen := FALSE;
    MES_Start := FALSE;
    IF HMI_Reset AND DI_SafetyOK THEN Dose_Step := IDLE; Dose_Alarm := ''; MES_Abort := FALSE; END_IF

END_CASE

(* step timers reset on every step change *)
IF Dose_Step <> FAST AND Dose_Step <> SLOW AND Dose_Step <> JOG THEN
    tStep(IN := FALSE);
    tNoFlow(IN := FALSE);
END_IF

DO_Beacon := Dose_Step = HELD OR Dose_Step = ABORTED;
DO_Horn := DO_Beacon AND NOT HMI_Reset;
