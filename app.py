
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import numpy as np 
import CoolProp



st.title('Krillemulles seje graf')

HEOS = CoolProp.AbstractState("HEOS", "R134a")
pmax=HEOS.p_critical()

# parameterize pressures from 1 bar to pmax by 20 points
psatL=np.linspace(1e5,pmax,20)
psatV=np.linspace(pmax,1e5,20)
# and instantiate enthalpy arrays
hsatL=np.empty([20])
hsatV=np.empty([20])

# make a for loop that update (calculate) refrigerant state along phase boundary
for k in range(0,len(psatL)):   
    HEOS.update(CoolProp.PQ_INPUTS, psatL[k],0)
    hsatL[k] = HEOS.hmass()
    HEOS.update(CoolProp.PQ_INPUTS, psatV[k],1)
    hsatV[k] = HEOS.hmass()

Te = st.slider('Evaporation temperature',-30,15,0)  # [C]
SH = st.slider('Superheat',1,30,5)  # [C]
Tc = st.slider('Condensation temperature',20,60,30) # [C]
SC = st.slider('Subcooling',1,30,5)  # [C]

# calculate evaporator (pe) and condenser (pc)
# pressures (temperatures in Kelvin)
# # CoolProp.QT_INPUTS are “quality” and “temperature”
HEOS.update(CoolProp.QT_INPUTS, 1, Te+273.15)
pe=HEOS.p()
HEOS.update(CoolProp.QT_INPUTS, 1, Tc+273.15)
pc=HEOS.p()

# Instantiate arrays for cycle points:
s=np.empty([5])
h=np.empty([5])
p=np.empty([5])
T=np.empty([5])

eta_vol=0.8
V_dot_geo = 12/3600 # [m3/s]

# state 1 @ pe and (Te+SH) (remember T in Kelvin)
# CoolProp.PT_INPUTS are pressure and temperature
HEOS.update(CoolProp.PT_INPUTS, pe, Te+273.15+SH)
h[1]=HEOS.hmass()
s[1]=HEOS.smass()
p[1]=HEOS.p()
T[1]=HEOS.T()
# calculate mass flow rate
m_dot = V_dot_geo*HEOS.rhomass()*eta_vol

eta_is = st.slider('Isentropisc effeciency',min_value=0.3, max_value=1.0, value=0.7) 

# state 2 @ pc and “h2”
# first calculate h2s (isentropic lossless 
# # process, s=constant)
HEOS.update(CoolProp.PSmass_INPUTS, pc, s[1])
h2s=HEOS.hmass()
# invoke isentropic efficiency of compressor
h[2]=h[1]+(h2s-h[1])/eta_is
# calculate other state variables
HEOS.update(CoolProp.HmassP_INPUTS, h[2], pc)
T[2]=HEOS.T()
s[2]=HEOS.smass()
p[2]=HEOS.p()

HEOS.update(CoolProp.PT_INPUTS, pc, Tc+273.15-SC)
h2s=HEOS.hmass()
T[3]=HEOS.T()
s[3]=HEOS.smass()
p[3]=HEOS.p()
h[3]=HEOS.hmass()

h[4]=h[3]

# and the state can be calculated as
HEOS.update(CoolProp.HmassP_INPUTS, h[4], pe)
T[4]=HEOS.T()
s[4]=HEOS.smass()
p[4]=HEOS.p()


h[0]=h[4]
s[0]=s[4]
p[0]=p[4]
T[0]=T[4]


fig, ax = plt.subplots()
ax.plot(h,p)
ax.plot(hsatL, psatL, label='Saturated Liquid')
ax.plot(hsatV, psatV, label='Saturated Vapor')
ax.set_yscale('log')
ax.set_xlabel('Enthalpy (J/kg)')
ax.set_ylabel('Pressure (Pa)')
ax.set_title('Log(p)-h Diagram')
ax.grid(True)
ax.legend() 
#plt.savefig("test.png")		# if you want to save

st.pyplot(fig)

W_dot = m_dot*(h[2]-h[1])

# evaporator capacity 
Q_dot_e = m_dot*(h[1]-h[4])

# condenser capacity
Q_dot_c = m_dot*(h[2]-h[3])

# coefficient of performance
COP = Q_dot_e/W_dot

st.metric(label="Compressor Power Consumption (W)", value=round(W_dot, 2))
st.metric(label="Cooling Capacity (W)", value=round(Q_dot_e, 2))
st.metric(label="Heating Capacity (W)", value=round(Q_dot_c, 2))
st.metric(label="Coefficient of Performance ", value=round(COP, 2))
