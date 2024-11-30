; Test program
mov $b 1        ; setup the multiplier

LOOP:
mul $b 10 $a    ; a <- 10 * B
add $b 1 $b     ; b <- b + 1
cmp $a 40       ; compare tra A e 40
jne LOOP        ; se A != 40 torna a LOOP
