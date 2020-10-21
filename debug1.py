# -*- coding: utf-8 -*-

import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import time
import urllib

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

# extend function 
def np_extend(a, b, axis = 0):
    if a is None:
        shape = list(b.shape)
        shape[axis] = 0
        a = np.array([]).reshape(tuple(shape))
    return np.append(a, b, axis)

# create label for each data
def num(lst,click):
    temp=[]
    for i in range(len(lst)):
        temp.append(click)
    return temp

# create label for each 

    
# in callbacks to transform the output value to logarithmic
#calculating wavelength
def wavelength(v):
    c=299790000 #light speed
    h=6.6256*10**-34#Planck's quantum
    e = 1.60217662 * 10**-19#amount of electron
    m= 9.10938356 * 10**-31# mass of electron
    loss=1/np.sqrt(1+v*e/(2*m*c**2))
    l=(h/np.sqrt(2*m*e*v))*loss
    return l

#bassel function n=0
def j0(x):
    return np.sin(x)/x

d_temp={'s': [], 'ctf': []}
d={}



app.layout = html.Div([
    html.H1('CTF (Contrast Transfer Function) Simulation'),
    html.Div(id='frame',style={'display': 'none'}),
    html.Div(id='d_ctf',style={'display': 'none'}),
    html.Div(id='change_select',style={'display': 'none'}),
    html.Div(id='defocus',style={'display': 'none'}),
    html.Div(id='ctf_data',style={'display': 'none'}),
    #html.Div(id='defocus_save',style={'display': 'none'}),
    html.Div([
        html.Div(id='update-defocus', style={'width': '10%', 'float': 'left', 'display': 'inline-block','margin-top': 20,'margin-right':0}),
        dcc.Input(id='defocus_input',  type='number',debounce=True,style={'float': 'left', 'width': '10%','margin-top':20,'margin-right':10}),
        html.Div([
            dcc.Slider(
                id='defocus_slide',
                marks={i: '{}'.format(i) for i in range(6)},
                max=5,
                
                dots=False,
                step=0.01,
                updatemode='drag'
            )
        ],style={'width': '35%', 'float': 'left', 'display': 'inline-block','margin-top': 20})
    ],),
    html.Div([
        html.Div(id='update-q', style={'width': '15%', 'float': 'left', 'display': 'inline-block','margin-left': 80,'margin-top': 20}),
        html.Div([
            dcc.Slider(
                id='phase',# amplitude contrast ratio
                marks={i:'{}'.format(i) for i in range(0,181,30)},
                max=180,
                
                step=0.1,
                updatemode='drag'
            )
        ],style={'width': '20%', 'float': 'left', 'display': 'inline-block','margin-top': 20})
    ],),
    html.Div(style={
        'borderBottom': 'thin lightgrey solid',
        'backgroundColor': 'rgb(250, 250, 250)',
        'padding': '30px 5px'
    }),
#2D distribution
    #html.Div([
    #    dcc.Graph(id='ctf_display2d')
    #],style={'width': '45%', 'float':'right','display': 'block','margin-left':0},className='one columns'),
    html.Div([
        dcc.Graph(id='ctf_display')
    ],className='six columns',style={ 'float':'left','display': 'block', 'padding': '0 1','margin-left':0}),
    html.Br(),
    html.Div([
        html.Button('creat a curve', id='button', n_clicks=0 ,className="three columns"),
        html.Div([
        dcc.Dropdown(
        id='trace_num',
        options=[{'label': 0, 'value': 0}],
            ),],className="three columns",style={'margin-left':50,'height':50}),
    ],className='six columns',style={'margin-top':70}),
    html.Div([
            #html.Label('phase shift'),
            #dcc.Input(id='delta', value=np.pi/2, type='number'),#applying phase shift
            html.Div([
                html.Label('Amplitude contrast ratio', style={'margin-right':20,'float':'left','width': '150%','font-size':12}),
                dcc.Input(id='q',  type='number',debounce=True,style={'margin-right':50,'float':'left','width': '120%'}),
            ], className="two columns"),
            html.Div([
                html.Label('Sample step', style={'margin-right':20,'float':'left','width': '150%'}), #chromatic aberration coefficient(mm)
                dcc.Input(id='step',  type='number',debounce=True,style={'margin-right':50,'float':'left','width': '120%'}), #chromatic aberration coefficient(mm)
            ], className="two columns"),
            html.Div([
                html.Label('Energy (keV)',style={'margin-right':20,'float':'left','width': '150%'}),
                dcc.Input(id='E',  type='number',debounce=True,style={'margin-right':50,'float':'left','width': '120%'}), # Energy(keV)
            ], className="two columns"),
              ],className="six columns",style={'padding': 10}),
    html.Div([
            html.Div([
                html.Label('Spherical aberration (mm)',style={'margin-right':0,'margin-left':0,'font-size':10}),
                dcc.Input(id='c',  type='number',debounce=True,style={'margin-right':0,'margin-left':0,'width': '120%'}), #Spherical aberration(mm)
            ], className="two columns"),
            html.Div([
                html.Label('B factor',style={'margin-right':0}),
                dcc.Input(id='B',  type='number',debounce=True,style={'margin-right':0,'width': '120%'}), #drift
            ], className="two columns"),
            html.Div([
                html.Label('A/pix',style={'margin-right':0}),
                dcc.Input(id='apix',  type='number',debounce=True,style={'margin-right':0,'width': '120%'}), #apix
            ], className="two columns"),
              ],className="six columns",style={'padding': 10}),
    html.Div([
            html.A('Download Selected CTF curve',id='download-link',download="ctf curve.csv",href="",target="_blank"),],className="six columns"),
])

#change the slider of defocus

@app.callback(Output(component_id='defocus_slide', component_property='value'),
              [Input(component_id='defocus_input', component_property='value')])
def defocus_slider_change(defocus_input):
    return defocus_input

# select defocus

#@app.callback([Output('defocus_save', 'children'),
#               Output('update-defocus', 'children'),
#               Output('defocus', 'children'),],
#              [Input('defocus_slide', 'value'),
#               Input('defocus_input', 'value')],
#               [State('defocus_save', 'children'),],)
#def select_defocus(defocus_slide,defocus_input,state):
#    #print(state)
#    lst=[defocus_slide,defocus_input]
#    #print(lst)
#    if state is None:
#        state=[0.5,0.5]
#        defocus=0.5
#    else:
#        if state[0]==lst[0]:
#            defocus=lst[1]
#        elif state[1]==lst[1]:
#            defocus=lst[0]
#        
#        state=lst
#    return state, 'Defocus(µm): {}'.format(defocus), defocus

@app.callback([Output('update-defocus', 'children'),
               Output('defocus', 'children'),],
              [Input('defocus_slide', 'value'),],)
def select_defocus(defocus_slide):
    defocus=defocus_slide
    print('set defocus')
    return 'Defocus(µm): {}'.format(defocus), defocus


# output the value
@app.callback(Output('update-q', 'children'),
              [Input('phase', 'value'),])
def display_value(q):
    return 'Phase shift (degree): {}'.format(q)

# update new parameters 
@app.callback([Output('defocus_input', 'value'),
                Output('q', 'value'),
                Output('E', 'value'),
                Output('c', 'value'),
                Output('phase', 'value'),
                Output('B', 'value'),
                Output('step', 'value'),
                Output('apix', 'value')],
                [Input('trace_num', 'value'),
                Input('frame', 'children'),])
def update_parameters(trace_num,frame):
    a=trace_num
    if d['ctf_data'][0] is None:
        data=[0.5, 0.05, 300, 2.7, 0, 100, 0.005, 1]
    else:
        if trace_num is not None:
            data=tuple(d['ctf_data'][trace_num])
        else:
            data=tuple(d['ctf_data'][-1])
    defocus,q,E,c,phase,B,step,apix=data
    print('set values')
    return defocus,q,E,c,phase,B,step,apix

# prepare ctf data
@app.callback([Output('d_ctf', 'children'),
                Output('ctf_data','children')],
               [Input('defocus', 'children'),
               Input('q', 'value'),
               Input('E', 'value'),
               Input('c', 'value'),
               Input('phase', 'value'),
               Input('B', 'value'),
               Input('step', 'value'),
               Input('apix', 'value')])
def display_input(defocus,q,E,c,phase,B,step,apix):
    if defocus is not None:
        #spatial frequency
        ctf_data=[defocus,q,E,c,phase,B,step,apix]
        print(defocus)
        range_ctf=0.5/apix
        s = np.arange(0.0, range_ctf, step)
        E=E*1000
        # change unit to A
        l=wavelength(E)*(10**10)
        c=c*(10**7)
        defocus=defocus*(10**4)
        #y is gama
        y=(2*np.pi)*((-c)*(l**3)*(s**4)/4+defocus*l*(s**2)/2)+phase/np.pi
        #envlope functions 
        #G1=np.exp(-(np.pi**2)*(0.0001*(c*(l**2)*(s**3)-defocus[0]*s))**2)
        #B factor
        G6=np.exp(-((B/4)*s*s))
        #voltage temporal coherence amplitude 
        #cc=cc*(10**7)#chromatic aberration coefficient(mm)
        #energy(eV)
        #G2=np.exp(-(np.pi**2)*(cc**2)*(l**2)*(s**4)*((dE/E)**2)/(16*np.log(2)))
        #CTF function 
        ctf=(np.sqrt(1-q**2)*np.sin(y)+q*np.cos(y))*G6
        d_ctf={'spatial': s, 'ctf': ctf}
        print('update values and curve')
        return d_ctf,ctf_data

# update data
# structure of d is {0:{spatial:[...],ctf:[...]}...trace:{0,...}}
@app.callback([Output('frame', 'children'),
                Output('change_select', 'children'),],
               [Input('ctf_data', 'children'),
               Input('d_ctf', 'children'),
               Input('button', 'n_clicks'),
               Input('trace_num', 'value'),])
def data_update(ctf_data,d_ctf,n_clicks,trace_num):
    global d
    print(ctf_data)
    if n_clicks == 0:
        d['0']=d_ctf
        d['ctf_data']=[ctf_data]
        d['trace']=[0]
    elif n_clicks>d['trace'][-1]:
        a=n_clicks
        d['trace'].append(a)
        d['ctf_data'].append(ctf_data)
        print(n_clicks)
        d[str(a)]=d_ctf
    elif (n_clicks==d['trace'][-1])& (n_clicks!=0):
        a=trace_num
        if trace_num is not None:
            d[str(a)]=d_ctf
            d['ctf_data'][a]=ctf_data
        else:
            num=d['trace'][-1]
            d[str(num)]=d_ctf
            d['ctf_data'][0]=ctf_data
    print(d['ctf_data'],d['trace'])
    data=d
    return d,data

# update dropdown
@app.callback(Output('trace_num', 'options'),
              [Input('frame', 'children'),],)
def display_trace(frame):
    return [{'label': i, 'value': i} for i in range(d['trace'][-1]+1)]

# select the data
#@app.callback(Output('change_select', 'children'),
#              [Input('trace_num', 'value'),
#               Input('frame', 'children'),
#               Input('d_ctf', 'children'),
#               Input('ctf_data', 'children'),])
#def change_select(trace_num, frame, d_ctf,ctf_data):
#    a=trace_num
#    if trace_num is not None:
#        d[str(a)]=d_ctf
#        d['ctf_data'][a]=ctf_data
#        data=d
#    else:
#        num=d['trace'][-1]
#        d[str(num)]=d_ctf
#        d['ctf_data'][0]=ctf_data
#        data=d
#    print('change select')
#    return data

# output the figure 1d
@app.callback(Output('ctf_display', 'figure'),
               [Input('change_select', 'children')])
def display_figure(change_select):
    #print(change_select)
    print('output')
    traces=[]
    len=change_select['trace'][-1]+1
    for i in range(len):
        line=change_select[str(i)]
        traces.append(go.Scatter(x=line['spatial'],y=line['ctf'],name='curve {}'.format(i),showlegend=True))
    return {
            'data': traces,
            'layout': go.Layout(
            xaxis={'title': 'Spatial frequency 1/A', 'range':[0,0.5]},
            yaxis={'range':[-1,1]},
            margin={'l': 40, 'b': 40, 't': 30, 'r': 0},
            annotations=[dict(x=1.145,y=1,text='hide curve',align='left', valign='top', showarrow=False, xref='paper',yref='paper',font=dict(size=18,color='#000'))],
            legend= dict(x=1,y=0.9,traceorder='normal', bgcolor='#E2E2E1',bordercolor='#FFFFFF',borderwidth=2,font=dict(size=15,color='#000')))
    }

#download the data
@app.callback(
    Output('download-link', 'href'),
    [Input('d_ctf', 'children')])
def update_download_link(d_ctf):
    dff = pd.DataFrame(d_ctf)
    csv_string = dff.to_csv(index=False, encoding='utf-8')
    csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
    return csv_string

# output the figure 2d
#@app.callback(Output('ctf_display2d', 'figure'),
#               [Input('defocus', 'children'),
#               Input('q', 'value'),
#               Input('E', 'value'),
#               Input('c', 'value'),
#               Input('phase', 'value'),
#               Input('B', 'value'),
#               Input('step', 'value'),
#               Input('apix', 'value'),
#               Input('change_select', 'children'),])
#def display_figure2d(defocus,q,E,c,phase,B,step,apix,d):
#    
#    timebefore=time.time()
#    x=d['trace'][-1]
#    step=int(1/step)
#    E=E*1000
#    # change unit to A
#    l=wavelength(E)*(10**10)
#    c=c*(10**7)
#    defocus=defocus*(10**4)
#    #CTF function
#    xe = np.linspace(-0.4,0.4,step)
#    ye = xe
#    ctf_2d=[]
#    
#    for i in xe:
#        temp=[]
#        for j in ye:
#            s=np.sqrt(i**2+j**2)
#            #y is gama
#            y=(2*np.pi)*((-c)*(l**3)*(s**4)/4+defocus*l*(s**2)/2)+phase/3.1415926535897932384626433
#            #envlope functions 
#            #G1=np.exp(-(np.pi**2)*(0.0001*(c*(l**2)*(s**3)-defocus[0]*s))**2)
#            #B factor
#            G6=np.exp(-((B/4)*s*s))
#            temp.append(abs((np.sqrt(1-q**2)*np.sin(y)*G6+q*np.cos(y))))
#        ctf_2d.append(temp)
#    return {
#        'data': [go.Heatmap(x = np.sort(xe),y = np.sort(ye),z = ctf_2d,colorscale='Greys')],
#        'layout': go.Layout(margin = {'t':100,'r':100,'b':100,'l':100},
#        width = 700, height = 700 )
#    }
if __name__ == '__main__':
    app.run_server(debug=True)