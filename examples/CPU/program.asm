; Test program
mov $a 0        ; setta il registro A a 0

LOOP:
add $a 10 $a    ; incrementa A di 10
cmp $a 40       ; compare tra A e 40
jne LOOP        ; se A != 40 torna a LOOP

mov #32 $a      ; sposta a in ram all'indirizzo 32