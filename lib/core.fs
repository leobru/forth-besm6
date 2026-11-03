: \ 140 PARSE DROP DROP ; IMMEDIATE
: ( 19 PARSE DROP DROP ; IMMEDIATE
\ FORTH for BESM-6: words defined in Forth, interpreted at startup.
\ Character codes are GOST 10859: blank 15, newline 140, ")" 19.
: IF ( -- orig ) ?BRANCH, ; IMMEDIATE
: AHEAD ( -- orig ) BRANCH, ; IMMEDIATE
: THEN ( orig -- ) >RESOLVE ; IMMEDIATE
: ELSE ( orig1 -- orig2 ) BRANCH, SWAP >RESOLVE ; IMMEDIATE
: BEGIN ( -- dest ) <MARK ; IMMEDIATE
: UNTIL ( dest -- ) ?BRANCH< ; IMMEDIATE
: AGAIN ( dest -- ) BRANCH< ; IMMEDIATE
: WHILE ( dest -- orig dest ) ?BRANCH, SWAP ; IMMEDIATE
: REPEAT ( orig dest -- ) BRANCH< >RESOLVE ; IMMEDIATE
: BL 15 ;
: CHAR ( "name" -- c ) BL WORD 1+ C@ ;
: [CHAR] CHAR LIT, ; IMMEDIATE
: ['] ' LIT, ; IMMEDIATE
: POSTPONE BL WORD FIND DUP 0= IF UNDEF THEN
  0< IF LIT, ['] COMPILE, THEN COMPILE, ; IMMEDIATE
\ DO compiles a call to (DO) and a cell for the LEAVE address.
: DO ['] (DO) COMPILE, HERE 0 , ; IMMEDIATE
: ?DO ['] (?DO) COMPILE, HERE 0 , ; IMMEDIATE
: LOOP ['] (LOOP) COMPILE, DUP 1+ , HERE SWAP ! ; IMMEDIATE
: +LOOP ['] (+LOOP) COMPILE, DUP 1+ , HERE SWAP ! ; IMMEDIATE
: 2DROP DROP DROP ;
: 2DUP OVER OVER ;
: TUCK SWAP OVER ;
: -ROT ROT ROT ;
: 2SWAP ROT >R ROT R> ;
: 2OVER >R >R 2DUP R> R> 2SWAP ;
: TRUE -1 ;
: FALSE 0 ;
: CELLS ;
: CELL+ 1+ ;
: CHARS ;
: CHAR+ 1+ ;
: NOT 0= ;
: ABS DUP 0< IF NEGATE THEN ;
: MIN 2DUP > IF SWAP THEN DROP ;
: MAX 2DUP < IF SWAP THEN DROP ;
: /MOD ( n1 n2 -- rem quot ) 2DUP MOD -ROT / ;
: 2* 1 LSHIFT ;
: U< 2DUP XOR 0< IF NIP 0< ELSE < THEN ;
: WITHIN ( n lo hi -- flag ) OVER - >R - R> U< ;
: VARIABLE CREATE 0 , ;
: CONSTANT CREATE , DOES> @ ;
: DECIMAL 10 BASE ! ;
: HEX 16 BASE ! ;
: OCTAL 8 BASE ! ;
: SPACE BL EMIT ;
: SPACES ( n -- ) BEGIN DUP 0> WHILE SPACE 1- REPEAT DROP ;
: COUNT ( c-addr -- c-addr+1 u ) DUP 1+ SWAP C@ ;
: (.) ( u -- ) BASE @ /MOD ?DUP IF RECURSE THEN >DIG EMIT ;
: . ( n -- ) DUP 0< IF [CHAR] - EMIT NEGATE THEN (.) SPACE ;
: U. ( u -- ) (.) SPACE ;
: ? ( addr -- ) @ . ;
: .S ( -- ) [CHAR] < EMIT DEPTH (.) [CHAR] > EMIT SPACE
  DEPTH 0 ?DO DEPTH I - 1- PICK . LOOP ;
: S" ( "text" -- c-addr u ) [CHAR] " PARSE
  STATE @ IF ['] (S") COMPILE, ", THEN ; IMMEDIATE
: ." ( "text" -- ) POSTPONE S" POSTPONE TYPE ; IMMEDIATE
: .( ( "text" -- ) [CHAR] ) PARSE TYPE ; IMMEDIATE
: FILL ( c-addr u c -- ) -ROT 0 ?DO 2DUP C! 1+ LOOP 2DROP ;
: ERASE ( c-addr u -- ) 0 FILL ;
: (ABORT") ( flag c-addr u -- ) ROT IF TYPE ABORT THEN 2DROP ;
: ABORT" POSTPONE S" POSTPONE (ABORT") ; IMMEDIATE
: WORDS ( -- ) LATEST @ BEGIN ?DUP WHILE
  DUP 1+ A>C COUNT 63 AND TYPE SPACE @ REPEAT CR ;
.( FORTH BESM-6) CR
