# P3-R1 — FINITE_WELL_MIXED_0D_COUPLING

Orden38a85593 autoriza un objeto físico distinto del reservoir prescritoP2.
Esta definición sustituye SOLO la interfaz futuraP3 de P1: los documentosP1–R5
y BC verificadas permanecen intactos como históricos y baselineP2.

## Volumen de control
Estado m,U,F,V: rho=m/V,e=U/m,T=e/cv,p=(gamma-1)*rho*e,Y=F/m.
W0D=(rho,0,p,Y): volumen homogéneo estacionario, sin momentum axial.
La aproximación representa conexión directa a una cara; sin Cd, puerto o apertura.
La energía total del contenido coincide con U porque su velocidad representativa
es cero. Energía cinética entrante se incorpora a interna bajo la hipótesis de
mezcla/disipación interna. No construir momentum temporal ni restar su cinética.

## Interfaz
Normal n apunta hacia afuera del tubo. Si n=-1, estados Riemann=(W0D,W1D);
si n=+1, (W1D,W0D). Una llamada HLLC contractual con fallback HLLE completo.
Gx=A*F_Riemann, Fout=n*Gx. d(m,U,F)0D=Fout[0,2,3], tubo recibe opuesto.
La orientación NO selecciona inflow/outflow: dirección emerge del flujo calculado.
El momentumGx[1] actúa normalmente en1D; fuerza/impulso externoFout[1] se
registra como reacción en cámara/pared, sin trabajo por pared estacionaria.
La energía es TODO el flujo numérico Euler, no m_dot*cvT ni otra entalpía por
rama. Especie TODO el componente Riemann, sin donor manual: HLLE puede difundir
un contacto, por lo que su razón especie/masa no debe sustituirse por otra.

## Gate R1 previo a P3B
C00: p100kPa,T0D300K,T1D299/300/301K,u0,Yambos.3, A.01m², ambas normales.
Referencia contacto Euler estacionario: flujosm/E/F nulos, presión transmitida.
C00B: mismos datos, Y0D.8/Y1D.2, velocidades±10^-1...±10^-5 y0m/s.
Guardar flujos y SM/método. Cada magnitud de flujom/E/F debe disminuir
estrictamente al reducir |u| en cada década y valer0 en reposo. Sin deadband.
Forward/reverse: p0D80/120kPa,p1D100kPa,T300K,u1D0; signo correspondiente,
vector HLLC íntegro, incrementos opuestos, especie HLLC coherente; fallback
probado por equivalencia de vector, no reemplazo manual. Regresión P2/P0,
revisión científica independiente requerida antes de actualizar volumen finito.

## Tiempo (solo después de R1 PASS)
CFL1D global. Sistema conjunto q=(C_i,m,U,F). Forward Euler o SSP-RK2 Heun:
q1=q+dtL(q,t), q2=q1+dtL(q1,t+dt), qnew=.5q+.5q2.
Mismo intercambio en RHS0D/1D de cada etapa, no congelarlo en el paso.
Rechazo conjunto ante inadmisibilidad o CFL del stage2, dt/2 hasta12 segúnP2.
Minmod y reconstrucciónP2 reutilizados; estado exterior para reconstrucción es
W0D del stage y el problema Riemann se resuelve solo al evaluar el flujo.
Ninguna segunda BC de presión/temperatura en la cara acoplada.
Para V(t), agregar únicamente-p*dV/dt a U y ledger; geometría1D estacionaria.
La etapa intermedia Euler extendida de Heun se valida a t+2dt antes de combinar
con estado inicial; el estado combinado usa V(t+dt). No hay momentum0D.
