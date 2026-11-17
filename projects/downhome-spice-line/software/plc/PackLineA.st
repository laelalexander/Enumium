(* ============================================================================
   PLC-602  PACK LINE A  -  PackML (ISA-TR88.00.02) state machine + line control
   BU-401 > FL-403 > CP-404 > IS-405 > LB-406/TT-407 > VS-408/RJ-408 > CW-409 >
   AT-410 > CE-411/CK-412 > CS-413 > PA-414 > PL-415
   Each OEM machine keeps its own controller and guarding. This PLC gives each
   one a PERMIT and reads READY/FAULT, runs the conveyor, the vision reject and
   the backup/starve logic, and exchanges the job with the MES.
   ============================================================================ *)

TYPE E_PackML : (
    STOPPED := 2, STARTING := 3, IDLE := 4, SUSPENDED := 5, EXECUTE := 6,
    STOPPING := 7, ABORTING := 8, ABORTED := 9, HOLDING := 10, HELD := 11,
    UNHOLDING := 12, SUSPENDING := 13, UNSUSPENDING := 14, RESETTING := 15,
    COMPLETING := 16, COMPLETE := 17, CLEARING := 1 );
END_TYPE

TYPE ST_Job :
STRUCT
    JobID        : STRING[20];
    SKU          : STRING[16];
    LotCode      : STRING[24];    (* DHyyjjj-B## + BEST BY text sent to TT-407 *)
    BlendBagID   : STRING[20];    (* released FIBC; BU-401 scan must match *)
    Container    : INT;           (* 1 shaker-250, 2 shaker-320, 3 jar-12 ... selects change-part recipe *)
    NetG         : REAL;
    TargetG      : REAL;          (* net x (1 + overfill) *)
    TareG        : REAL;
    UnitsOrdered : DINT;
    CaseCount    : INT;
    SpeedUPM     : REAL;          (* 80 shakers / 45 jars, from line balance *)
    Valid        : BOOL;
END_STRUCT
END_TYPE

VAR_GLOBAL
    MES_Job         : ST_Job;
    MES_BagScanOK   : BOOL;         (* MES confirms FIBC at BU-401 is released and matches job *)
    MES_LabelOK     : BOOL;         (* MES confirms first-off label/lot code check signed *)
    Cmd_Start, Cmd_Stop, Cmd_Reset, Cmd_Hold, Cmd_Unhold, Cmd_Abort, Cmd_Clear : BOOL;
    LineA_State     : E_PackML := STOPPED;
    LineA_Good      : DINT;         (* accepted by CW-409 *)
    LineA_RejVision : DINT;
    LineA_RejWeight : DINT;         (* counted by CW-409 over OPC UA, mirrored here *)
    LineA_Cases     : DINT;
    LineA_StopReason: INT;          (* first-out, for OEE in MES *)
    LineA_MachSpeed : REAL;         (* upm command to FL-403 *)
END_VAR

PROGRAM PackLineA
VAR
    Faults      : WORD;
    AllReady    : BOOL;
    Starved     : BOOL;
    Blocked     : BOOL;
    tStarve     : TON;
    tBlock      : TON;
    tStep       : TON;
    tRejChk     : TON;      (* reject must be confirmed by PE-406 within 500 ms *)
    rVis        : R_TRIG;
    rCase       : R_TRIG;
    rReset      : R_TRIG;
    RejQueue    : ARRAY[0..15] OF BOOL;   (* shift register: vision fail -> pusher, 6 pitches *)
    rPitch      : R_TRIG;
    i           : INT;
END_VAR

(* ---------- machine status ---------- *)
Faults.0  := FL403_FAULT;  Faults.1 := CP404_FAULT;  Faults.2 := IS405_FAULT;  Faults.3 := LB406_FAULT;
Faults.4  := CW409_FAULT;  Faults.5 := CE411_FAULT;  Faults.6 := CK412_FAULT;  Faults.7 := CS413_FAULT;
Faults.8  := PA414_FAULT;  Faults.9 := PL415_FAULT;  Faults.10 := CV417_FAULT; Faults.11 := TT407_FAULT;
Faults.12 := CW409_BIN_FULL OR CW409_BIN_DOOR;   (* reject bin must be locked and not full: CCP verification *)
Faults.13 := NOT SR602_OK;
Faults.14 := tRejChk.Q;   (* pusher fired but PE-406 did not see the reject *)

AllReady := FL403_READY AND CP404_READY AND IS405_READY AND LB406_READY AND CW409_READY
            AND CE411_READY AND CK412_READY AND CS413_READY AND PA414_READY AND PL415_READY;

(* first-out stop reason *)
IF LineA_StopReason = 0 AND Faults <> 0 THEN
    FOR i := 0 TO 15 DO
        IF (WORD_TO_DINT(SHR(Faults, i)) MOD 2) = 1 AND LineA_StopReason = 0 THEN LineA_StopReason := i + 1; END_IF;
    END_FOR;
END_IF;

(* starve: filler hopper low with no bag running; block: accumulation full *)
tStarve(IN := FL403_HOPPER_LOW AND NOT BU401_RUN, PT := T#20S);   Starved := tStarve.Q;
tBlock(IN := PE408_BLOCKED, PT := T#5S);                           Blocked := tBlock.Q;

rReset(CLK := Cmd_Reset OR PB602_RESET);

(* ---------- global transitions ---------- *)
IF Faults.13 OR Cmd_Abort THEN
    IF LineA_State <> ABORTED THEN LineA_State := ABORTING; END_IF;
ELSIF Faults <> 0 AND (LineA_State = EXECUTE OR LineA_State = SUSPENDED OR LineA_State = STARTING) THEN
    LineA_State := HOLDING;
ELSIF Cmd_Stop AND LineA_State <> STOPPED AND LineA_State <> ABORTED THEN
    LineA_State := STOPPING;
END_IF;

CASE LineA_State OF
STOPPED:
    IF rReset.Q THEN LineA_State := RESETTING; END_IF;

RESETTING:
    LineA_StopReason := 0;
    IF AllReady AND SR602_OK THEN LineA_State := IDLE; END_IF;

IDLE:
    (* job, released bag and signed first-off label are all required before start *)
    IF Cmd_Start AND MES_Job.Valid AND MES_BagScanOK AND MES_LabelOK THEN
        tStep(IN := FALSE); LineA_State := STARTING;
    END_IF;

STARTING:
    CV417_RUN_CMD := TRUE;
    tStep(IN := TRUE, PT := T#3S);           (* conveyor first, then machines, downstream to upstream *)
    IF tStep.Q THEN tStep(IN := FALSE); LineA_State := EXECUTE; END_IF;

EXECUTE:
    LineA_MachSpeed := MES_Job.SpeedUPM;
    IF Starved OR Blocked THEN LineA_State := SUSPENDING; END_IF;
    IF LineA_Good >= MES_Job.UnitsOrdered THEN LineA_State := COMPLETING; END_IF;

SUSPENDING:  LineA_State := SUSPENDED;
SUSPENDED:
    LineA_MachSpeed := 0.0;
    IF NOT Starved AND NOT Blocked THEN LineA_State := UNSUSPENDING; END_IF;
UNSUSPENDING: LineA_State := EXECUTE;

HOLDING:     LineA_State := HELD;
HELD:
    IF Faults = 0 AND (Cmd_Unhold OR rReset.Q) THEN LineA_State := UNHOLDING; END_IF;
UNHOLDING:   LineA_State := EXECUTE;

COMPLETING:
    (* run out: stop filler, keep downstream running until accumulation empties *)
    LineA_MachSpeed := 0.0;
    tStep(IN := NOT PE409_BLOCKED, PT := T#30S);
    IF tStep.Q THEN tStep(IN := FALSE); LineA_State := COMPLETE; END_IF;
COMPLETE:
    MES_Job.Valid := FALSE; MES_BagScanOK := FALSE; MES_LabelOK := FALSE;
    IF rReset.Q THEN LineA_State := RESETTING; END_IF;

STOPPING:    LineA_MachSpeed := 0.0; LineA_State := STOPPED;
ABORTING:    LineA_MachSpeed := 0.0; LineA_State := ABORTED;
ABORTED:
    IF Cmd_Clear AND SR602_OK THEN LineA_State := CLEARING; END_IF;
CLEARING:    LineA_State := STOPPED;
END_CASE;

(* ---------- outputs ---------- *)
CV417_RUN_CMD := LineA_State = STARTING OR LineA_State = EXECUTE OR LineA_State = SUSPENDED
                 OR LineA_State = COMPLETING OR LineA_State = UNSUSPENDING OR LineA_State = UNHOLDING;
FL403_PERMIT  := LineA_State = EXECUTE AND NOT PE402_BLOCKED;      (* no fill into a backed-up capper *)
BU401_START   := (LineA_State = EXECUTE OR LineA_State = SUSPENDED) AND MES_BagScanOK AND NOT FL403_HOPPER_HIGH;
UN402_START   := LineA_State = EXECUTE AND NOT PE401_BLOCKED;
CP404_PERMIT  := CV417_RUN_CMD;
IS405_PERMIT  := CV417_RUN_CMD;
LB406_PERMIT  := CV417_RUN_CMD AND NOT TT407_FAULT;                 (* never label without a lot code *)
CW409_PERMIT  := CV417_RUN_CMD;
CE411_PERMIT  := CV417_RUN_CMD;
CK412_PERMIT  := CV417_RUN_CMD;
CS413_PERMIT  := CV417_RUN_CMD;
PA414_PERMIT  := CV417_RUN_CMD;
PL415_PERMIT  := LineA_State <> ABORTED AND SR602_OK;

(* vision reject: shift register clocked by vision trigger eye, pusher 6 pitches downstream *)
rVis(CLK := PE405_BLOCKED);
IF rVis.Q THEN
    FOR i := 15 TO 1 BY -1 DO RejQueue[i] := RejQueue[i - 1]; END_FOR;
    RejQueue[0] := VS408_FAIL;
    IF VS408_FAIL THEN LineA_RejVision := LineA_RejVision + 1; END_IF;
END_IF;
RJ408_FIRE := RejQueue[6] AND PE405_BLOCKED;
tRejChk(IN := (RJ408_FIRE OR tRejChk.IN) AND NOT PE406_BLOCKED, PT := T#500MS);

rCase(CLK := PE410_BLOCKED);
IF rCase.Q THEN LineA_Cases := LineA_Cases + 1; END_IF;

SL602_RED   := LineA_State = HELD OR LineA_State = ABORTED OR LineA_State = STOPPED;
SL602_AMBER := LineA_State = SUSPENDED OR LineA_State = IDLE OR LineA_State = COMPLETE;
SL602_GREEN := LineA_State = EXECUTE;
SL602_HORN  := LineA_State = ABORTING OR Faults.12;
END_PROGRAM
