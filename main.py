import sys
import glob
import pickle
from minio_loader import get_pickles, put_file
from create_dae import create_dae
from xml_builder import build_xml

DAE_NAME = 'model.dae'
XML_NAME = 'model.xml'
PICKLE_NAME = 'total_xml_data.pickle'


def create_model(path):
    pickles = glob.glob(path + '*.pickle')

    if len(pickles) > 0:
        print('Found pickles:')
        for pkl in pickles:
            print(pkl)
    else:
        print('Pickles not found.')
        return
    
    levels = []
    for pkl in pickles:
        with open(pkl, 'rb') as f:
            data = pickle.load(f)
        levels.append(data)

    lvls_for_xml = [value for dictionary in levels for value in dictionary.values()]
    xml_str = build_xml(lvls_for_xml)
    full_path = path + XML_NAME
    with open(full_path, "w") as f:
        f.write(xml_str)

    create_dae(levels, path, DAE_NAME)

if __name__ == "__main__":

    args = sys.argv

    if len(args) >= 2:
        if args[1] == '-local':
            PATH = '/home/egor/Desktop/EnterAR/PickleTestNew/test/'
            create_model(PATH)

        if args[1] == '-minio':
            PATH = '/home/egor/Desktop/EnterAR/PickleTestNew/test/'
            get_pickles(PATH, PICKLE_NAME)
    else:
        PATH = '/data/'
        get_pickles(PATH, PICKLE_NAME)
        create_model(PATH)
        XML_full_path = PATH + XML_NAME 
        DAE_full_path = PATH + DAE_NAME
        put_file(XML_full_path, XML_NAME)
        put_file(DAE_full_path, DAE_NAME)
