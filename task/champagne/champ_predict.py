# %%

import pandas as pd
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F
from torch.utils.data import TensorDataset, DataLoader
import torchkeras
from plotly import graph_objects as go
from sklearn.preprocessing import MinMaxScaler

# %%

# 导入数据
# 数据下载：https://www.kaggle.com/kankanashukla/champagne-data
df = pd.read_csv('covid.csv', index_col=0)
df.head()

# %%

# 数据预览
# fig = go.Figure()
# fig.add_trace(go.Scatter(x=df.index, y=df['Sales'], name='Sales'))
# fig.show()

# %%

# 数据处理
# 标准化
scaler = MinMaxScaler()
predict_field = 'Scaler'
df[predict_field] = scaler.fit_transform(df['Sales'].values.reshape(-1, 1))
df.head()

#%%
def create_dataset(data: list, time_step: int):
    arr_x, arr_y = [], []
    for i in range(len(data) - time_step - 1):
        x = data[i: i + time_step]
        y = data[i + time_step]
        arr_x.append(x)
        arr_y.append(y)
    return np.array(arr_x), np.array(arr_y)


device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
print('Device:', device)

time_step = 8
X, Y = create_dataset(df[predict_field].values, time_step)
# 转化成 tensor->(batch_size, seq_len, feature_size)
X = torch.tensor(X.reshape((-1, time_step, 1)), dtype=torch.float).to(device)
Y = torch.tensor(Y.reshape((-1, 1, 1)), dtype=torch.float).to(device)
print('Total datasets: ', X.shape, '-->', Y.shape)

# 划分数据
split_ratio = 0.8
len_train = int(X.shape[0] * split_ratio)
X_train, Y_train = X[:len_train, :, :], Y[:len_train, :, :]
print('Train datasets: ', X_train.shape, '-->', Y_train.shape)

# 构建迭代器
batch_size = 10
ds = TensorDataset(X, Y)
dl = DataLoader(ds, batch_size=batch_size, num_workers=0)
ds_train = TensorDataset(X_train, Y_train)
dl_train = DataLoader(ds_train, batch_size=batch_size, num_workers=0)

x, y = next(iter(dl_train))
# for x, y in dl_train:
print(x.shape)
print(y.shape)
    # break


# %%

# 定义模型
class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.lstm = nn.LSTM(input_size=1, hidden_size=6, num_layers=3, batch_first=True)
        self.fc = nn.Linear(in_features=6, out_features=1)

    def forward(self, x):
        # x is input, size (batch_size, seq_len, input_size)
        x, _ = self.lstm(x)
        # x is output, size (batch_size, seq_len, hidden_size)
        x = x[:, -1, :]
        x = self.fc(x)
        x = x.view(-1, 1, 1)
        return x


# %%
##############################
model_style = 1
##############################

if model_style == 0:
    # torchkeras API 训练方式
    model = torchkeras.Model(Net())
    model.summary(input_shape=(time_step, 1))
    model.compile(loss_func=F.mse_loss, optimizer=torch.optim.Adam(model.parameters(), lr=1e-2), device=device)
    dfhistory = model.fit(epochs=50, dl_train=dl_train, log_step_freq=20)
    # 模型评估
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dfhistory.index, y=dfhistory['loss'], name='loss'))
    fig.show()
    y_pred = model.predict(dl).detach().cpu().numpy().squeeze()

else:
    def train_step(model, features, labels):
        # 正向传播求损失
        predictions = model.forward(features)
        loss = loss_function(predictions, labels)
        # 反向传播求梯度
        loss.backward()
        # 参数更新
        optimizer.step()
        optimizer.zero_grad()
        return loss.item()


    def train_model(model, epochs):
        for epoch in range(1, epochs + 1):
            list_loss = []
            for features, labels in dl_train:
                lossi = train_step(model, features, labels)
                list_loss.append(lossi)
            loss = np.mean(list_loss)
            if epoch % 10 == 0:
                print('epoch={} | loss={} '.format(epoch, loss))


    # 测试一个batch
    model = Net().to(device)
    loss_function = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-2)

    features, labels = next(iter(dl_train))
    loss =  train_step(model, features, labels)
    print(loss)

    train_model(model, 50)
    y_pred = model.forward(X).detach().cpu().numpy().squeeze()
# %%



# %%

# 预测验证预览
y_true = Y.cpu().numpy().squeeze()

fig = go.Figure()
fig.add_trace(go.Scatter(y=y_true, name='y_true'))
fig.add_trace(go.Scatter(y=y_pred, name='y_pred'))
fig.show()

# %%

# 自定义训练方式




# %%
"""
# 预测验证预览
y_pred = model.forward(X)
y_p_pred = y_pred.detach().cpu().numpy().squeeze()
Y_p_true = Y.cpu().squeeze()
fig = go.Figure()
fig.add_trace(go.Scatter(y=Y_p_true, name='y_true'))
fig.add_trace(go.Scatter(y=y_p_pred, name='y_pred'))
fig.show()

# %%

# 外推20个点
n = 20

list_y_pre = []
x = X[-1].view(1, 1, time_step)

for n in range(1, n + 1):
    y = model.forward(x)
    # y = y.view(-1,1,1)
    list_y_pre.append(y.item())
    x = torch.cat([x, y], dim=2)
    x = x[:, :, 1:]

y_p2_pred = np.concatenate((y_p_pred,np.array(list_y_pre)))
fig = go.Figure()
fig.add_trace(go.Scatter(y=Y_p_true, name='y_true'))
fig.add_trace(go.Scatter(y=y_p2_pred, name='y_pred'))
fig.show()
"""
