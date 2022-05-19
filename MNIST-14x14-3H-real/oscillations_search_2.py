from sympy import unflatten
import torch
from model import PCMLP
import os
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import pickle 
from scipy.sparse.linalg import eigs
os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"


def RhoCloseToOne(w,l,over,under,beta,gamma,tol = 10**-3):
    for eig in w:
        if abs(1-abs(eig)) < tol:
            if (beta,gamma) not in l:
                l.append((beta,gamma))
        elif abs(eig) > 1 :
            if (beta,gamma) not in over:
                over.append((beta,gamma))
        else:
            if (beta,gamma) not in under:
                under.append((beta,gamma))
        if l and over and under:
            break

for alpha in [0.01,0.05,0.1,0.25]:

    betaR = list(np.arange(0,1,0.01))[1:]
    gammaR = list(np.arange(0,1,0.01))[1:]

    threshold = []

    model= PCMLP(0.33,alpha,0.5,0.2)
    checkpointPhase = torch.load(os.path.join('models',f"PC_E19_I4.pth"))
    model.load_state_dict(checkpointPhase["module"])
    for name, p in model.named_parameters():
        tmp = p.detach().numpy()
        if name=='fcAB.weight':
            W12 = p.detach().numpy()
        if name=='fcBA.weight':
            W21 = p.detach().numpy()
        if name=='fciA.weight':
            W01 = p.detach().numpy()
        if name=='fcAi.weight':
            W10 = p.detach().numpy()

    good_params = []
    over_one = []
    under_one = []
    d = W12.shape[1]
    print(d)

    for beta in betaR:
        for i, gamma in enumerate(gammaR):
            if beta + gamma > 1:
                pass
            else:
               

                A11 = (1-beta-gamma) * np.eye(d)
                A12 = beta * W21
                A21 = (1-beta-gamma) * gamma * W12 + alpha/d * W21.T
                A22 = gamma * beta * W12.dot(W21) + (1-gamma) * np.eye(d) - alpha/d * W21.T.dot(W21)

                A = np.block([[A11,A12],[A21,A22]])

                w = np.linalg.eigvals(A) # ie spectral radius
                RhoCloseToOne(w,good_params,over_one,under_one,beta,gamma,tol = 10**-6)


    np.save(os.path.join('oscillations_parameters_setup',f'alternative_good_params_{alpha}.npy'),good_params)
    np.save(os.path.join('oscillations_parameters_setup',f'alternative_over_params_{alpha}.npy'),over_one)
    np.save(os.path.join('oscillations_parameters_setup',f'alternative_under_params_{alpha}.npy'),under_one)


    good_params = np.load(os.path.join('oscillations_parameters_setup',f'alternative_good_params_{alpha}.npy'))
    over_one = np.load(os.path.join('oscillations_parameters_setup',f'alternative_over_params_{alpha}.npy'))
    under_one =  np.load(os.path.join('oscillations_parameters_setup',f'alternative_under_params_{alpha}.npy'))
    plt.figure()
    plt.scatter(*zip(*over_one),color='blue',label='rho > 1',alpha=0.35,linewidths=0.2)
    plt.scatter(*zip(*under_one),color='green',label='rho < 1',alpha=0.35,linewidths=0.2)
    plt.scatter(*zip(*good_params),color='red',label='rho = 1',alpha=0.35,linewidths=0.2)
    x = np.linspace(0,1,100)
    plt.plot(x,1-x,linestyle='dashed',label='$\lambda+\\beta = 1$',color='red')
    plt.xlabel('$\lambda$')
    plt.xlim((0,1))
    plt.ylim((0,1))
    plt.ylabel('$\\beta$')
    plt.title(f'Potential oscillations for $\\alpha = {alpha}$')
    plt.legend()
    plt.savefig(os.path.join('oscillations_parameters_setup',f'alternative_potential_good_parameters_{alpha}.png'))
    plt.close()

    osci_eigv = []
    for beta,gamma in good_params:
        

        A11 = (1-beta-gamma) * np.eye(d)
        A12 = beta * W21
        A21 = (1-beta-gamma) * gamma * W12 + alpha/d * W21.T
        A22 = gamma * beta * W12.dot(W21) + (1-gamma) * np.eye(d) - alpha/d * W21.T.dot(W21)
        A = np.block([[A11,A12],[A21,A22]])

        w, v = np.linalg.eig(A)
        for i,eig in enumerate(w):
            if np.isreal(eig) or abs(1-abs(eig)) >= 10**-3 : 
                pass
            else:
                #print(eig)
                osci_eigv.append((beta,gamma,v[i]))

    osci_imgs = [(beta,gamma,np.real(y[:196])) for beta,gamma,y in osci_eigv]

    unflattened_imgs = dict([(f"im{i})",(img[0],img[1],img[2].reshape((14,14)))) for i, img in enumerate(osci_imgs)]) #img[0:1] are parameters beta and gamma
    with open(os.path.join('oscillations_parameters_setup',f'alternative_params_dictionary_{alpha}.pkl'), 'wb') as f:
        pickle.dump(unflattened_imgs, f)

    unflattened_imgs_list = [img for _,img in unflattened_imgs.items()]
    print(len(unflattened_imgs_list))
    for i,img in enumerate(unflattened_imgs_list):
        _,_,img = img
        plt.imsave(os.path.join('oscillations_parameters_setup',f'alternative_img_{alpha}_{i}.png'),img, cmap='gray')
