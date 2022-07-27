from email.policy import default
import os
# import pcr.constants.constant as constant
from ctypes import windll

# Path definitions
PCR_PATH = "C:/mPCR"
PROTOCOL_PATH = PCR_PATH + "/protocols"
RECENT_PROTOCOL_FILENAME = "recent_protocol_python.txt"


class Protocol():
    """사용중인 PCR Protocol 관리를 위한 클래스

    Params:
        name: `str`
            Protocol name
        actions: `list`
            A list of actions(lines) in the PCR Protocol

    Note:
        The parameter 'actions' must be shaped with multiple `dict` like this.
        [
            {'Label': 1, 'Temp': 60, 'Time': 5},
            {'Label': 'SHOT', 'Temp': 0, 'Time': 0},
            {'Label' :'GOTO','Temp' : 2,'Time' : 1},
            ...
        ]
    """
    def __init__(self, name, actions):
        self.name = name
        self.actions = actions
        self.shot_labels = []
        
        for action in self.actions:
            if action["Time"] == 0:
                self.shot_labels.append(action["Label"])
                
        print(self.shot_labels)

    def __getitem__(self, idx):
        return self.actions[idx]
    
    def __str__(self):
        _str = 'name : ' + self.name + '\n'
        for action in self.actions:
            _str += f'Label : {action["Label"]:>4}, Temp : {action["Temp"]:>3}, Time : {action["Time"]:>3}\n'
        return _str

    def __len__(self):
        return len(self.actions)
    
    def get_label_action(self, label):
        for action in self.actions:
            if action["Label"] == label:
                return action
        else:
            return action
        

# Default pcr protocol actions
default_protocol = Protocol('Default', [
    {'Label' : 1, 'Temp' : 60, 'Time' : 5}, 
    {'Label' : 2, 'Temp' : 90, 'Time' : 5}, 
    {'Label' : 3, 'Temp' : 65, 'Time' : 5},
    {'Label' :'GOTO','Temp' : 2,'Time' : 2},
    {'Label' : 4, 'Temp' : 40, 'Time' : 5}
])

# PCR Protocol Error definitions
class PCRProtocolError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg

def list_protocols():
    """Return list of *.txt file(protocol file) names
    """
    # filtering extension
    files = list(filter(lambda x : x[-4:] == '.txt', os.listdir(PROTOCOL_PATH)))
    protocols = [file[:-4] for file in files]   # slicing extension
    return protocols

def save_protocol(protocol):
    path = os.path.join(PROTOCOL_PATH, f"{protocol.name}.txt") # protocol path
    try:
        actions = check_protocol(protocol)    # check protocol
    except PCRProtocolError as err:
        windll.user32.MessageBoxW(0, f"{err}", u"PCR Protocol error", 0)

    with open(path, 'w') as file:   # open protocol file
        # actions to text list ('label'\t'temp'\t'time')
        lines = ['{}\t{}\t{}'.format(*action.values()).strip() for action in actions]
        # write text list
        file.write('\n'.join(lines))

def load_protocol(protocol_name):
    path = os.path.join(PROTOCOL_PATH, protocol_name) # protocol path

    with open(path + ".txt", 'r') as file:   # open protocol file
        protocol_keys = ['Label', 'Temp', 'Time'] # protocol keys 
        lines = file.read().strip().split('\n')   # read text lines
        
        # list to dict (text to actions)  
        actions = [dict(zip(protocol_keys, line.split('\t'))) for line in lines] 

        # check protocol and return protocol
        try:
            actions = check_protocol(actions)
        except PCRProtocolError as err:
            windll.user32.MessageBoxW(0, f"{err}", u"PCR Protocol error", 0)
            # If rasied error while loading Protocol..
            # Set default protocol...
            return default_protocol
        
        return Protocol(protocol_name, actions)


def check_protocol(protocol):
    line_number = 0     # For debugging message
    current_label = 0   # For check normal actions
    found_goto = False  # For check multiple 'GOTO' labels
    actions = []

    # Check Protocol (save & load)
    for line in protocol:
        line_number += 1

        try:
            # unpacking action to (label, temp, time)
            label, temp, time = list(map(lambda x : int(x) if type(x) is str and x.lstrip('-').isdecimal() else x, list(line.values())))
        except Exception as err:
            raise PCRProtocolError(f"Invalid protocol data, line {line_number}")
        
        # Check the line
        if type(label) is int: # Check normal label
            current_label += 1
            
            if label != current_label:
                raise PCRProtocolError(f"Invalid label number, line {line_number}")
            
            if not 10 <= temp <= 105:
                raise PCRProtocolError(f"Invalid temperature value (Temp must be 10~105), line {line_number}")
            
            if not 0 <= time <= 65000:
                raise PCRProtocolError(f"Invalid time value (Time must be 0(shot)~105), line {line_number}")
        
        elif label == 'GOTO': # Check GOTO label
            if found_goto:
                raise PCRProtocolError(f"Invalid GOTO label ('GOTO' label is cannot use multiple), line {line_number}")
            else:   found_goto = True
            
            if not current_label:
                raise PCRProtocolError(f"Invalid GOTO label ('GOTO' label is cannot first line), line {line_number}")
            
            if not 1 <= time <= 100:
                raise PCRProtocolError(f"Invalid GOTO count(1~100), line {line_number}")
            
        elif label == 'SHOT': # Check SHOT label
            raise PCRProtocolError(f"Invalid label ('SHOT' label is being implemented), line {line_number}")
        
        else:
            raise PCRProtocolError(f"Invalid label, line {line_number}")
        
        actions.append({'Label' : label, 'Temp' : temp, 'Time' : time})
    return actions

def loadRecentProtocolName():
    try:
        with open(PCR_PATH + '\\' + RECENT_PROTOCOL_FILENAME, 'r') as file:
            protocol_name = file.readline()
            file.close()
        
        return protocol_name
    except FileNotFoundError as err:
        return

def saveRecentProtocolName(protocol_name=''):
    try:
        with open(PCR_PATH + '\\' + RECENT_PROTOCOL_FILENAME, 'w') as file:
            file.write(protocol_name)
            file.close()
        
        return protocol_name
    except FileNotFoundError as err:
        return
    
if __name__ == "__main__":
    protocol = load_protocol("shot_test_protocol")
    save_protocol(protocol)