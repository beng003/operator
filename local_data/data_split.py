import pandas as pd
import numpy as np
from secretflow.utils.simulation.datasets import dataset
import os


df = pd.read_csv(dataset('bank_marketing_full'), sep=';')
df['uid'] = df.index + 1
df_alice = df.iloc[:, np.r_[0:8, -1]].sample(frac=0.9)
df_bob = df.iloc[:, 8:].sample(frac=0.9)
# 获取当前脚本所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
alice_path = current_dir + '/alice/alice_bank_flow.csv'
bob_path = current_dir + '/bob/bob_bank_flow.csv'
print(alice_path)
df_alice.reset_index(drop=True).to_csv(alice_path, index=False)
df_bob.reset_index(drop=True).to_csv(bob_path, index=False)
