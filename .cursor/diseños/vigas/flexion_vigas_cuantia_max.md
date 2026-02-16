DISEÑO DE VIGAS POR FLEXION (METODO E-060 - CRITERIO DE CUANTIA MAXIMA - unidades en kg/cm2 y cm)

1. Calculo de profundidad de bloque de compresion (a) [Ref. Art. 10.2.7.1]
   
   a = d - sqrt(d^2 - 2 * Mu / (phi_flexion * 0.85 * fc * b))
   
   donde:
   d = distancia desde la fibra extrema en compresion hasta el centroide del acero en tension (cm)
   Mu = momento ultimo en kg-cm (kg-cm)
   fc = resistencia a la compresion del concreto en kg/cm2 (kg/cm2)
   b = ancho de la viga en cm (cm)
   phi_flexion = factor de reduccion de momento = 0.9 [Ref. Art. 9.3.2.1]
   
2. Limite de la profundidad de bloque de compresion (a_max) por el metodo de cuantia maxima [Ref. Art. 10.3.4]
   
   c_balanceada = e_c * d / (e_c + fy / Es) [Ref. Art. 10.3.2]

   a_balanceada = b1 * c_balanceada [Ref. Art. 10.2.7.1]

   a_max = 0.75 * a_balanceada [Ref. Art. 10.3.4]

   donde:
   e_c = deformación unitaria del concreto en compresión = 0.003 [Ref. Art. 10.2.3]
   d = peralte efectivo (cm)
   fy = resistencia a la fluencia del acero en kg/cm2 (kg/cm2)
   Es = modulo de elasticidad del acero = 2000000 kg/cm2 [Ref. Art. 8.5.5]
   b1 = 0.85 para fc <= 280 kg/cm2; para fc > 280, b1 disminuye 0.05 por cada 70 kg/cm2 de exceso, sin ser menor de 0.65 [Ref. Art. 10.2.7.3]
   c_balanceada = profundidad del eje neutro balanceado (cm)
   a_balanceada = profundidad del bloque de compresion balanceado (cm)
   a_max = profundidad maxima del bloque de compresion (cm)

3. Verificar el tipo de seccion (VSR o VDR) [Ref. Art. 10.3.5]
   
   Si a <= a_max, entonces la seccion es de tipo VSR
   Si a > a_max, entonces la seccion es de tipo VDR
   
   donde:
   a = profundidad de bloque de compresion en cm (cm)
   a_max = profundidad de bloque de compresion en cm (cm)
   
4. Calculo de area de acero requerida (As) [Ref. Art. 10.2]
   
   Si la seccion es de tipo VSR, entonces:

   Acero requerido

   As = Mu / (phi_flexion * fy * (d-a/2))

   Mu = Momento ultimo (kg-cm)
   phi_flexion = 0.9 [Ref. Art. 9.3.2.1]
   fy = fluencia del acero (kg/cm2)
   d = peralte efectivo (cm)
   a = profundidad de bloque de compresion calculada en Paso 1 (cm)

   Si la seccion es de tipo VDR (Refuerzo en compresion requerido) [Ref. Art. 10.3.3]:

   Momento que resiste el concreto (como VSR maxima)

   Muc = 0.85 * fc * b * a_max * (d - a_max/2) [Ref. Art. 10.2.7]

   Muc = Momento que resiste el concreto en kg-cm (kg-cm)
   phi_flexion = factor de reduccion de momento = 0.9
   fc = resistencia a la compresion del concreto en kg/cm2 (kg/cm2)
   b = ancho de la viga en cm (cm)
   a_max = profundidad de bloque de compresion en cm (cm)
   d = distancia desde la fibra extrema en compresion hasta el centroide del acero en tension (cm)

   Momento remanente a cubrir  por el acero a compresion y traccion adicional

   Mus = Mu - Muc

   Mus = Momento remanente a cubrir  por el acero a compresion y traccion adicional en kg-cm (kg-cm)
   Mu = Momento ultimo en kg-cm (kg-cm)
   Muc = Momento que resiste el concreto en kg-cm (kg-cm)

   Acero de compresion As'

   As' = Mus / (phi_flexion * (fs' - 0.85 * fc) * ( d - d' ))

   As' = Acero de compresion en cm2 (cm2)
   Mus = Momento remanente a cubrir  por el acero a compresion y traccion adicional en kg-cm (kg-cm)
   phi_flexion = factor de reduccion de momento = 0.9
   fs' = resistencia a la fluencia del acero a compresion en kg/cm2 (kg/cm2)
   d' = distancia desde la fibra extrema en compresion hasta el centroide del acero a compresion (cm)

   Calculo de fs' [Ref. Art. 10.2.4]
   
   c_max = a_max / b1

   fs' = es * e_c * ((c_max - d') / c_max) <= fy
   
   fs' = esfuerzo en el acero de compresion (kg/cm2)
   es = modulo de elasticidad del acero = 2000000 kg/cm2
   e_c = deformación unitaria del concreto en compresión = 0.003
   c_max = profundidad del eje neutro (cm)
   d' = distancia desde la fibra extrema en compresion hasta el centroide del acero a compresion (cm)
   fy = resistencia a la fluencia del acero en kg/cm2 (kg/cm2)

   Acero de traccion base As1

   As1 = Muc / (phi_flexion * fy * (d - a_max / 2))
   
   As1 = Acero de traccion adicional en cm2 (cm2)
   Muc = Momento que resiste el concreto en kg-cm (kg-cm)
   phi_flexion = factor de reduccion de momento = 0.9
   fy = resistencia a la fluencia del acero en kg/cm2 (kg/cm2)
   d = distancia desde la fibra extrema en compresion hasta el centroide del acero en tension (cm)
   a_max = profundidad de bloque de compresion en cm (cm)

   Acero de traccion adicional As2

   As2 = Mus / (phi_flexion * fy * (d - d'))
   
   As2 = Acero de traccion adicional en cm2 (cm2)
   Mus = Momento remanente a cubrir  por el acero a compresion y traccion adicional en kg-cm (kg-cm)
   phi_flexion = factor de reduccion de momento = 0.9
   fy = resistencia a la fluencia del acero en kg/cm2 (kg/cm2)
   d = distancia desde la fibra extrema en compresion hasta el centroide del acero en tension (cm)
   d' = distancia desde la fibra extrema en compresion hasta el centroide del acero a compresion (cm)

   Acero total As

   As = As1 + As2

   As = Acero total en cm2 (cm2)
   As1 = Acero de traccion adicional en cm2 (cm2)
   As2 = Acero de traccion adicional en cm2 (cm2)

5. Verificar el acero minimo [Ref. Art. 10.5.1 y Anexo II]
   
   Para VSR:
   
   Asmin1 = 0.7 * sqrt(fc) * b * d / fy [Ec. 10-3 del Anexo II]

   Asmin = Acero minimo en cm2 (cm2)
   fc = resistencia a la compresion del concreto en kg/cm2 (kg/cm2)
   fy = resistencia a la fluencia del acero en kg/cm2 (kg/cm2)
   b = ancho de la viga en cm (cm)
   d = peralte efectivo (cm)

   Asmin2 = 1.4 / fy * b * d

   Asmin = Acero minimo en cm2 (cm2)
   fy = resistencia a la fluencia del acero en kg/cm2 (kg/cm2)
   b = ancho de la viga en cm (cm)
   d = peralte efectivo (cm)

   Asmin = max(Asmin1, Asmin2)

   Condicion: As >= Asmin
   (Nota: Si el area de acero proporcionada es al menos un tercio superior a la requerida por analisis, no es necesario satisfacer este requisito [Ref. Art. 10.5.3])

   donde:
   As = Acero en traccion en cm2 (cm2)
   Asmin = Acero minimo en cm2 (cm2)

   Para VDR:
   Asmin1 = 0.7 * sqrt(fc) * b * d / fy [Ec. 10-3 del Anexo II]

   Asmin = Acero minimo en cm2 (cm2)
   fc = resistencia a la compresion del concreto en kg/cm2 (kg/cm2)
   fy = resistencia a la fluencia del acero en kg/cm2 (kg/cm2)
   b = ancho de la viga en cm (cm)
   d = peralte efectivo (cm)

   Asmin2 = 1.4 / fy * b * d

   Asmin = Acero minimo en cm2 (cm2)
   fy = resistencia a la fluencia del acero en kg/cm2 (kg/cm2)
   b = ancho de la viga en cm (cm)
   d = peralte efectivo (cm)

   Asmin = max(Asmin1, Asmin2)
   donde:
   As = Acero en traccion en cm2 (cm2) = As1 + As2
   Asmin = Acero minimo en cm2 (cm2)

6. Verificar el acero maximo [Ref. Art. 10.3.5]

   Para VSR:
   Asmax = (0.85 * fc * a_max / fy) * b

   Asmax = Acero maximo en cm2 (cm2)
   fc = resistencia a la compresion del concreto en kg/cm2 (kg/cm2)
   a_max = profundidad de bloque de compresion en cm (cm)
   fy = resistencia a la fluencia del acero en kg/cm2 (kg/cm2)
   b = ancho de la viga en cm (cm)

   As <= Asmax
   
   Para VDR:
   Asmax = (0.85 * fc * a_max * b / fy) + (As' * fs' / fy)

   Condicion: As <= Asmax

7. Verificar Momento de agrietamiento (Mcr) [Ref. Art. 10.5.1]

   El refuerzo provisto debe resistir al menos 1.2 veces el momento de agrietamiento.

   Mcr = fr * Ig / yt [Ref. Art. 9.6.2.3 Ec. 9-11]
   fr = 2 * sqrt(fc) [Ref. Art. 9.6.2.3 y Anexo II]
   Ig = b * h^3 / 12 (Inercia bruta)
   yt = h / 2 (Distancia a la fibra extrema en traccion)

   donde:
   fc = resistencia a la compresion del concreto en kg/cm2 (kg/cm2)
   b = ancho de la viga en cm (cm)
   h = altura de la viga en cm (cm)
   Mcr = Momento de agrietamiento en kg-cm (kg-cm)
   fr = Modulo de rotura del concreto en kg/cm2 (kg/cm2)
   Ig = Momento de inercia de la seccion en cm4 (cm4)
   yt = Distancia desde la fibra extrema en tension hasta el centroide de la seccion en cm (cm)

   Calculo de la resistencia de diseño provista (phi * Mn):

   Para VSR:
    a_real = As * fy / (0.85 * fc * b)
    donde:
    a_real = profundidad de bloque de compresion (cm)
    As = acero en traccion (cm2)
    fy = resistencia a la fluencia del acero (kg/cm2)
    fc = resistencia a la compresion del concreto (kg/cm2)
    b = ancho de la viga (cm)

    phi_Mn = phi_flexion * As * fy * (d - a_real/2)

    donde:
    phi_flexion = factor de reduccion de momento = 0.9 [Ref. Art. 9.3.2.1]
    As = Acero en traccion en cm2 (cm2)
    fy = resistencia a la fluencia del acero en kg/cm2 (kg/cm2)
    d = distancia desde la fibra extrema en compresion hasta el centroide del acero en tension (cm)
    a_real = profundidad de bloque de compresion (cm)
    d = peralte efectivo (cm)
    phi_Mn = momento nominal resistente (kg-cm)
    
    Condicion Final: phi_Mn >= 1.2 * Mcr [Ref. Art. 10.5.1]

    Para VDR:

    A = 0.85 * fc * b
    B = As' * Es * e_c - As * fy
    C = - As' * Es * e_c * b1 * d'

    a_real = (-B + sqrt(B^2 - 4 * A * C)) / (2 * A)

    donde:
    A = coeficiente de la ecuacion cuadratica
    B = coeficiente de la ecuacion cuadratica
    C = coeficiente de la ecuacion cuadratica
    e_c = deformación unitaria del concreto en compresión = 0.003
    a_real = profundidad de bloque de compresion (cm)
    Es = modulo de elasticidad del acero = 2000000 kg/cm2
    As' = Acero de compresion en cm2 (cm2)
    b1 = factor de reduccion de momento = 0.85 para fc <= 280 kg/cm2 y b1 = 0.85 - 0.05*(fc-280)/70 para fc > 280 kg/cm2
    d' = distancia desde la fibra extrema en compresion hasta el centroide del acero a compresion (cm)
    fy = resistencia a la fluencia del acero en kg/cm2 (kg/cm2)
    fc = resistencia a la compresion del concreto en kg/cm2 (kg/cm2)
    b = ancho de la viga en cm (cm)

    fs' = Es * e_c * (1 - d' * b1 / a_real) <= fy

    fs' = resistencia a la fluencia del acero a compresion en kg/cm2 (kg/cm2)
    Es = modulo de elasticidad del acero = 2000000 kg/cm2
    e_c = deformación unitaria del concreto en compresión = 0.003
    d' = distancia desde la fibra extrema en compresion hasta el centroide del acero a compresion (cm)
    b1 = factor de reduccion de momento = 0.85 para fc <= 280 kg/cm2 y b1 = 0.85 - 0.05*(fc-280)/70 para fc > 280 kg/cm2
    a_real = profundidad de bloque de compresion (cm)
    fy = resistencia a la fluencia del acero en kg/cm2 (kg/cm2)

    phi_Mn = phi_flexion * (0.85 * fc * b * a_real * (d - a_real/2) + As' * fs' * (d - d'))

    Condicion Final: phi_Mn >= 1.2 * Mcr [Ref. Art. 10.5.1]

    donde (VDR):
    phi_flexion = factor de reduccion de momento = 0.9 [Ref. Art. 9.3.2.1]
    fc = resistencia a la compresion del concreto en kg/cm2 (kg/cm2)
    b = ancho de la viga en cm (cm)
    a_real = profundidad de bloque de compresion (cm)
    d = distancia desde la fibra extrema en compresion hasta el centroide del acero en tension (cm)
