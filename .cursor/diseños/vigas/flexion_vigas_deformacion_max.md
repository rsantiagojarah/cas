DISEÑO DE VIGAS POR FLEXION (METODO E-060 - CRITERIO DE DEFORMACION MAXIMA = 0.004 - unidades en kg/cm2 y cm)

1. Calculo de profundidad de bloque de compresion (a)
   
   a = d - sqrt(d^2 - 2 * Mu / (phi_flexion * 0.85 * fc * b))
   
   donde:
   d = distancia desde la fibra extrema en compresion hasta el centroide del acero en tension (cm)
   Mu = momento ultimo en kg-cm (kg-cm)
   fc = resistencia a la compresion del concreto en kg/cm2 (kg/cm2)
   b = ancho de la viga en cm (cm)
   phi_flexion = factor de reduccion de momento = 0.9
   
2. Limite de la profundidad de bloque de compresion (a_max) por el metodo de deformacion maxima = 0.004
   
   eps_max = deformacion maxima en el acero en tension = 0.004

   c_max = e_c * d / (e_c + eps_max)
   
   a_max = b1 * c_max (donde b1 = 0.85 para fc <= 280 kg/cm2 y b1 = 0.85 - 0.05*(fc-280)/70 para fc > 280 kg/cm2)
   
   donde:
   d = distancia desde la fibra extrema en compresion hasta el centroide del acero en tension (cm)
   eps_max = deformacion maxima en el acero en tension = 0.004
   e_c = deformación unitaria del concreto en compresión = 0.003
   c_max = profundidad del eje neutro en cm (cm)
   a_max = profundidad de bloque de compresion en cm (cm)
   
3. Verificar el tipo de seccion (VSR o VDR)
   
   Si a <= a_max, entonces la seccion es de tipo VSR
   Si a > a_max, entonces la seccion es de tipo VDR
   
   donde:
   a = profundidad de bloque de compresion en cm (cm)
   a_max = profundidad de bloque de compresion en cm (cm)
   
4. Calculo de area de acero requerida (As)
   
   Si la seccion es de tipo VSR, entonces:

   Acero requerido

   As = Mu / (phi_flexion * fy * (d-a/2))

   Mu = Momento ultimo en kg-cm (kg-cm)
   phi_flexion = factor de reduccion de momento = 0.9
   fy = resistencia a la fluencia del acero en kg/cm2 (kg/cm2)
   d = distancia desde la fibra extrema en compresion hasta el centroide del acero en tension (cm)
   a = profundidad de bloque de compresion en cm (cm)

   Si la seccion es de tipo VDR, entonces:

   Momento que resiste el concreto

   Muc = 0.85 * fc * b * a_max * (d - a_max/2)

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

   Calculo de fs'
   
   fs' = es * e_c * ((c_max - d') / c_max) <= fy
   
   fs' = resistencia a la fluencia del acero a compresion en kg/cm2 (kg/cm2)
   es = modulo de elasticidad del acero = 2000000 kg/cm2
   e_c = deformación unitaria del concreto en compresión = 0.003
   c_max = profundidad de bloque de compresion en cm (cm)
   d' = distancia desde la fibra extrema en compresion hasta el centroide del acero a compresion (cm)
   fy = resistencia a la fluencia del acero en kg/cm2 (kg/cm2)

   Acero de traccion adicional As1

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

5. Verificar el acero minimo
   
   Asmin = 0.7 * (fc^0.5) * b * d / fy

   Asmin = 1.4 / fy * b * d

   Asmin = Acero minimo en cm2 (cm2)
   fc = resistencia a la compresion del concreto en kg/cm2 (kg/cm2)
   fy = resistencia a la fluencia del acero en kg/cm2 (kg/cm2)
   b = ancho de la viga en cm (cm)
   d = distancia desde la fibra extrema en compresion hasta el centroide del acero en tension (cm)

   Asmin = max(Asmin1, Asmin2)

   Para VSR:
   As >= Asmin 
   donde:
   As = Acero en traccion en cm2 (cm2)
   Asmin = Acero minimo en cm2 (cm2)

   Para VDR:
   Asmin = 0.7 * (fc^0.5) * b * d / fy
   As >= Asmin
   donde:
   As = Acero en traccion en cm2 (cm2) = As1 + As2
   Asmin = Acero minimo en cm2 (cm2)

6. Verificar el acero maximo

   Para VSR:
   Asmax = (0.85 * fc * a_max / fy) * b

   Asmax = Acero maximo en cm2 (cm2)
   fc = resistencia a la compresion del concreto en kg/cm2 (kg/cm2)
   a_max = profundidad de bloque de compresion en cm (cm)
   fy = resistencia a la fluencia del acero en kg/cm2 (kg/cm2)
   b = ancho de la viga en cm (cm)

   As <= Asmax
   
   Para VDR:
   Asmax = 0.85 * fc * a_max * b / fy + As' * f's / fy

   Asmax = Acero maximo en cm2 (cm2)
   fc = resistencia a la compresion del concreto en kg/cm2 (kg/cm2)
   a_max = profundidad de bloque de compresion en cm (cm)
   b = ancho de la viga en cm (cm)
   fy = resistencia a la fluencia del acero en kg/cm2 (kg/cm2)
   As' = Acero de compresion en cm2 (cm2)
   f's = resistencia a la fluencia del acero a compresion en kg/cm2 (kg/cm2)

   As <= Asmax

7. Verificar Momento de agrietamiento (Mcr)
   
   Mcr = fr * Ig / yt

   fr = 2 * sqrt(fc)

   Ig = b * h^3 / 12
   
   yt = h / 2

   donde:
   fc = resistencia a la compresion del concreto en kg/cm2 (kg/cm2)
   b = ancho de la viga en cm (cm)
   h = altura de la viga en cm (cm)
   Mcr = Momento de agrietamiento en kg-cm (kg-cm)
   fr = Modulo de rotura del concreto en kg/cm2 (kg/cm2)
   Ig = Momento de inercia de la seccion en cm4 (cm4)
   yt = Distancia desde la fibra extrema en tension hasta el centroide de la seccion en cm (cm)

   Para VSR:
    a = As * fy / (0.85 * fc * b)
    a = profundidad de bloque de compresion en cm (cm)
    As = Acero en traccion en cm2 (cm2)
    fy = resistencia a la fluencia del acero en kg/cm2 (kg/cm2)
    fc = resistencia a la compresion del concreto en kg/cm2 (kg/cm2)
    b = ancho de la viga en cm (cm)

    phi_flexion * Mn = phi_flexion * As * fy * (d - a/2)

    donde:
    phi_flexion = factor de reduccion de momento = 0.9
    Mn = Momento nominal en kg-cm (kg-cm)
    As = Acero en traccion en cm2 (cm2)
    fy = resistencia a la fluencia del acero en kg/cm2 (kg/cm2)
    d = distancia desde la fibra extrema en compresion hasta el centroide del acero en tension (cm)
    a = profundidad de bloque de compresion en cm (cm)

    phi_flexion * Mn >= 1.2 * Mcr

    Para VDR:

    A = 0.85 * fc * b
    B = As' * Es * e_c - As * fy
    C = - As' * Es * e_c * b1 * d'

    a = (-B + sqrt(B^2 - 4 * A * C)) / (2 * A)

    donde:
    A = coeficiente de la ecuacion cuadratica
    B = coeficiente de la ecuacion cuadratica
    C = coeficiente de la ecuacion cuadratica
    e_c = deformación unitaria del concreto en compresión = 0.003
    a = profundidad de bloque de compresion en cm (cm)
    Es = modulo de elasticidad del acero = 2000000 kg/cm2
    As' = Acero de compresion en cm2 (cm2)
    b1 = factor de reduccion de momento = 0.85 para fc <= 280 kg/cm2 y b1 = 0.85 - 0.05*(fc-280)/70 para fc > 280 kg/cm2
    d' = distancia desde la fibra extrema en compresion hasta el centroide del acero a compresion (cm)
    fy = resistencia a la fluencia del acero en kg/cm2 (kg/cm2)
    fc = resistencia a la compresion del concreto en kg/cm2 (kg/cm2)
    b = ancho de la viga en cm (cm)

    fs' = Es * e_c * (1 - d' * b1 / a) <= fy
    fs' = resistencia a la fluencia del acero a compresion en kg/cm2 (kg/cm2)
    Es = modulo de elasticidad del acero = 2000000 kg/cm2
    e_c = deformación unitaria del concreto en compresión = 0.003
    d' = distancia desde la fibra extrema en compresion hasta el centroide del acero a compresion (cm)
    b1 = factor de reduccion de momento = 0.85 para fc <= 280 kg/cm2 y b1 = 0.85 - 0.05*(fc-280)/70 para fc > 280 kg/cm2
    a = profundidad de bloque de compresion en cm (cm)
    fy = resistencia a la fluencia del acero en kg/cm2 (kg/cm2)

    phi_flexion * Mn = phi_flexion (0.85 * fc * b * a * (d - a/2) + As' * fs' * (d - d'))
    donde:
    phi_flexion = factor de reduccion de momento = 0.9
    Mn = Momento nominal en kg-cm (kg-cm)
    fc = resistencia a la compresion del concreto en kg/cm2 (kg/cm2)
    b = ancho de la viga en cm (cm)
    a = profundidad de bloque de compresion en cm (cm)
    d = distancia desde la fibra extrema en compresion hasta el centroide del acero en tension (cm)
    As' = Acero de compresion en cm2 (cm2)
    fs' = resistencia a la fluencia del acero a compresion en kg/cm2 (kg/cm2)

    phi_flexion * Mn >= 1.2 * Mcr

    


