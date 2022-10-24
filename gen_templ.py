import requests
import yaml
import json

ft=open('template_data.yml','r')
data = yaml.load(ft, Loader=yaml.FullLoader)
ft.close()

headers={}
headers["Content-Type"]="application/json"
headers["Authorization"]='Token {}'.format(data['token'])

resp=requests.get(data['apiurl']+"orgs/"+data['orgid']+"/sites", headers=headers)
for site in resp.json():
    if site['name'] == data['site']:
        siteid=site['id']
        break

resp=requests.get(data['apiurl']+"sites/"+siteid+"/setting", headers=headers)
current_vars=resp.json()

template={}

template['type']=data['type']
template['name']=data['name']
template['org_id']=data['orgid']

template['dns_servers']=list(data['dns'])
template['ntp_servers']=list(data['ntp'])

template['path_preferences']={}
template['path_preferences']['overlay']={}
template['path_preferences']['overlay']['strategy']='ecmp'
template['path_preferences']['overlay']['paths']=[]

if data['type']=='gateway':
    template['path_preferences']['underlay']={}
    template['path_preferences']['underlay']['strategy']='ordered'
    template['path_preferences']['underlay']['paths']=[]

template['port_config']={}
for wan in data['wans']:
    template['port_config'][wan['if']]={}
    template['port_config'][wan['if']]['name']=wan['name']
    template['port_config'][wan['if']]['usage']='wan'
    template['port_config'][wan['if']]['wan_type']='broadband'
    template['port_config'][wan['if']]['vpn_paths']={}
    template['port_config'][wan['if']]['vpn_paths'][data['hub_name']+'-'+wan['hub']+'.OrgOverlay']={}
    if data['type']=='spoke':
        template['port_config'][wan['if']]['vpn_paths'][data['hub_name']+'-'+wan['hub']+'.OrgOverlay']['role']='spoke'
        template['port_config'][wan['if']]['vpn_paths'][data['hub_name']+'-'+wan['hub']+'.OrgOverlay']['bfd_profile']='broadband'
    else:
        template['port_config'][wan['if']]['vpn_paths'][data['hub_name']+'-'+wan['hub']+'.OrgOverlay']['role']='hub'
    tmp_path={}
    tmp_path['type']='vpn'
    tmp_path['name']=data['hub_name']+'-'+wan['hub']+'.OrgOverlay'
    template['path_preferences']['overlay']['paths'].append(tmp_path)
    if data['type']=='gateway':
        tmp_path={}
        tmp_path['type']='wan'
        tmp_path['name']=wan['name']
        template['path_preferences']['underlay']['paths'].append(tmp_path)
    template['port_config'][wan['if']]['ip_config']={}
    template['port_config'][wan['if']]['ip_config']['type']='static'
    template['port_config'][wan['if']]['ip_config']['ip']='{{'+data['name']+'_'+wan['name']+'_'+'ip}}'
    template['port_config'][wan['if']]['ip_config']['netmask']='/{{'+data['name']+'_'+wan['name']+'_'+'mask}}'
    template['port_config'][wan['if']]['ip_config']['gateway']='{{'+data['name']+'_'+wan['name']+'_'+'gw}}'
    current_vars['vars'][data['name']+'_'+wan['name']+'_'+'ip']=wan['ip']
    current_vars['vars'][data['name']+'_'+wan['name']+'_'+'mask']=wan['mask']
    current_vars['vars'][data['name']+'_'+wan['name']+'_'+'gw']=wan['gw']

print(json.dumps(current_vars['vars'], indent=4))
print(json.dumps(template, indent=4))

resp=requests.put(data['apiurl']+"sites/"+siteid+"/setting", json=current_vars, headers=headers)
print(resp)

resp=requests.post(data['apiurl']+"orgs/"+data['orgid']+"/gatewaytemplates", json=template, headers=headers)
print(resp)
