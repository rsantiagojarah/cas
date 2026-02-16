DISEÑO POR CORTANTE DE VIGAS (METODO E-060 - unidades en kg/cm2 y cm)

1. CALCULO DE Vc [Ref. Art. 11.3.1]

Vc = 0.53 * (fc**0.5) * b * d

donde:
fc = resistencia a la compresion del concreto (kg/cm2)
b = ancho de la viga (cm)
d = peralte efectivo (cm)

2. CALCULO DE V_max [Ref. Art. 11.3.1]

Vs_max = 2.1 * fc **0.5 * b * d
donde:
Vs_max = cortante que resiste el acero maximo (kg)
fc = resistencia a la compresion del concreto (kg/cm2)
b = ancho de la viga (cm)
d = peralte efectivo (cm)

Vn_max = Vc + Vs_max

donde:
Vn_max = cortante que resiste el concreto y el acero maximo (kg)
Vc = cortante que resiste el concreto (kg)
b = ancho de la viga (cm)
d = peralte efectivo (cm)

1. CALCULO DE Vs [Ref. Art. 11.3.1]

Vs = Vu / phi_cortante - Vc

donde:
phi_cortante = factor de reduccion de cortante = 0.85 [Ref. Art. 9.3.2.1]
Vs = cortante que resiste el acero (kg)
Vu = cortante ultimo (kg)
Vc = cortante que resiste el concreto (kg)

4. CONSIDERACIONES PARA EL DISEÑO:

- Si Vu <= Vc/2 * phi_cortante, entonces no se requiere refuerzo por cortante.
  Av_s / s = 0.0

- Si Vc/2 * phi_cortante < Vu <= phi_cortante * V_max, entonces se requiere refuerzo por cortante.
  Av_s / s = Vs / (fy * d)
  donde:
  Av_s / s = area de acero por cortante (cm2) / espaciamiento entre estribos (cm)
  Vs = cortante que resiste el acero (kg)
  fy = resistencia a la fluencia del acero (kg/cm2)
  d = peralte efectivo (cm)

- Si Vu > phi_cortante * Vn_max, entonces la seccion es insegura y debe aumentarse el peralte o la resistencia del concreto.
  Av_s / s = None

5. VERIIFIACION Vs_max [Ref. Art. 11.3.1]

Vs_max = 2.1 * fc **0.5 * b * d

donde:
Vs_max = cortante que resiste el acero maximo (kg)
fc = resistencia a la compresion del concreto (kg/cm2)
b = ancho de la viga (cm)
d = peralte efectivo (cm)

Vs <= Vs_max

6. SEPARACION DE ESTRIBOS [Ref. Art. 11.3.1]

Smax = d / 2
Smax = 60 cm

S = min(Smax, S1, S2)

Si Vs > 1.1 * fc **0.5 * b * d, entonces:

    Smax = S / 2

donde:
Smax = espaciamiento maximo entre estribos (cm)

7. CUANTIA MINIMA DE ESTRIBOS [Ref. Art. 11.3.1]

Av_s_min1 = 0.2 * fc ** 0.5 * b * s / fy

Av_s_min2 = 3.5 * b * s / fy

Av_s_min = max(Av_s_min1, Av_s_min2)

donde:
Av_s_min1 = area de acero por cortante minimo (cm2)
Av_s_min2 = area de acero por cortante minimo (cm2)
fc = resistencia a la compresion del concreto (kg/cm2)
b = ancho de la viga (cm)
s = espaciamiento entre estribos (cm)
fy = resistencia a la fluencia del acero (kg/cm2)
Av_s_min = area de acero por cortante minimo (cm2)