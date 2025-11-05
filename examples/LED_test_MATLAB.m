a = arduiono;
pin = 'D11';

for k = 1:6
    writeDigitalPin(a, pin, 1);
    pause(5);
    writeDigitalPin(a, pin, 0);
    pause(5);
end

clear a