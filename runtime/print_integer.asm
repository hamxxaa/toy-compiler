section .data
    buffer db 20 dup(0)  ; Buffer to hold the string representation of the integer
    global newline
    newline db 10        ; Newline character

section .bss
    global num
    num resd 1           ; Reserve space for the integer variable

section .text
    global print_integer ; Make the function globally accessible

print_integer:
    ; Input: integer value in [num]
    ; Output: prints the integer to stdout

    mov eax, dword [num] ; Load the integer into eax
    lea edi, [buffer+19] ; Point to the end of the buffer
    mov byte [edi], 0    ; Null-terminate the string
    mov ecx, 10          ; Divisor for base 10

    ; Check if the number is negative
    test eax, eax        ; Check if eax is negative
    jns convert_loop     ; If positive, proceed normally

    ; Handle negative numbers
    neg eax              ; Convert to positive



convert_loop:
    dec edi              ; Move the pointer back
    xor edx, edx         ; Clear edx for division
    div ecx              ; Divide eax by 10, result in eax, remainder in edx
    add dl, '0'          ; Convert remainder to ASCII
    mov [edi], dl        ; Store the ASCII character
    test eax, eax        ; Check if eax is zero
    jnz convert_loop     ; If not zero, continue loop

    cmp dword [num], 0
    jge positive
    
    dec edi              ; Move back first
    mov byte [edi], '-'  ; Store '-' at the correct place

positive:
    ; Calculate the length of the string
    lea esi, [edi]       ; Pointer to the start of the string
    lea edx, [buffer+19] ; Pointer to the end of the buffer
    sub edx, esi         ; Calculate the length



    ; Print the string (using 32-bit system calls)
    mov eax, 4           ; syscall: write
    mov ebx, 1           ; file descriptor: stdout
    mov ecx, esi         ; pointer to the start of the string
    int 0x80             ; invoke the system call

    ret