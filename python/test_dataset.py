import sys
sys.path.append('python')
from model.dataset import load_dataset

sequences, labels = load_dataset('data/conjunctions/dataset.csv')
print('First sequence shape:', sequences[0].shape)
print('First label:', labels[0])
