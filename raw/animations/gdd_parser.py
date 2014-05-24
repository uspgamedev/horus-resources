
import copy
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("input", help="Path to input file")
parser.add_argument("output", help="Path to output file")
args = parser.parse_args()

valid_properties = { 'fps' }
properties = {}

result_table = {}
current_animation = None

def finalize_current_animation():
    global current_animation
    if current_animation:
        result_table[current_animation['name']] = {
            'period': len(current_animation['frames']) / properties['fps'],
            'frames': current_animation['frames']
        }
        current_animation = None
    
def start_new_animtion(animation_name):
    properties['fps'] = 10.0
    properties['compose'] = False
    global current_animation
    current_animation = {
        'name': animation_name,
        'effect': {},
        'frames': [],
    }
    
def parse_data(input):
    finalize_current_animation()
    start_new_animtion(input)
    
def parse_property(input):
    split = input.split(' ', 1)
    name = split[0]
    if name not in valid_properties:
        raise Exception("Unknown property name: " + name)
    
    if len(split) > 1:
        properties[name] = float(split[1])
    else:
        properties[name] = True

def transform_color(s):
    x = int(s, 16)
    return (x >> 16) % 256, (x >> 8) % 256, x % 256
        
valueparser = {
    'number': lambda x: int(x),
    'color': transform_color,
    'alpha': lambda x: float(x),
    'position': lambda x: map(float, x.split(' ')),
    'size': lambda x: map(float, x.split(' ')),
    'rotation': lambda x: float(x),
    'mirror': lambda x: x,
}
        
def parse_ring(input):
    split = input.split(' ', 1)
    name = split[0]
       
    current_frame = copy.deepcopy(current_animation['effect'])
    
    import re
    for mod in re.findall(r"\[(.*?)\]", split[1]):
        mod_name, mod_value = mod.split(' ', 1)
        current_frame[mod_name] = valueparser[mod_name](mod_value)
    
    if 'alpha' in current_frame:
        if 'color' not in current_frame:
            current_frame['color'] = [1, 1, 1]
        current_frame['color'][3] = current_frame['alpha']
        del current_frame['alpha']
        
    if 'mirror' in current_frame:
        if current_frame['mirror'].find('h') > -1:
            current_frame['mirrorh'] = True
        if current_frame['mirror'].find('v') > -1:
            current_frame['mirrorv'] = True
        del current_frame['mirror']
    
    if name == "effect":
        if properties['compose']:
            raise Exception("NYI")
        else:
            for k in current_frame:
                current_animation['effect'][k] = current_frame[k]

    elif name == "frame":            
        current_animation['frames'].append(current_frame)
        
def parse_chain(input):
    split = input.split(' ', 1)
    name = split[0]
    assert(name == "number")
    
    for number in split[1].split(' '):
        current_frame = copy.deepcopy(current_animation['effect'])
        current_frame['number'] = int(number)
        current_animation['frames'].append(current_frame)
        
syntax_mapping = {
    '#': lambda x: None,
    '$': parse_data,
    '@': parse_property,
    '+': parse_ring,
    '%': parse_chain
}
        
for line in open(args.input):
    command = line.strip()
    if not command: continue
    syntax_mapping[command[0]](command[1:])
        
finalize_current_animation()
import json
with open(args.output, 'w') as output_file:
    json.dump(result_table, output_file, indent=4, separators=(',', ': '))