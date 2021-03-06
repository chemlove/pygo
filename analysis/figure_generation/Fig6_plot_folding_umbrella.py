#!/usr/bin/python2.4

import numpy
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib
import cPickle
import optparse
import plot_dG
import plot_dG_solution

def main():
    lam = [.1, .15, .2, .25, .3, .35, .4, .45, .5, .55, .6, .65, .7]
    Q_files = ['/home/edz3fz/proteinmontecarlo/results/1PGB/surface/umbrella_lambda%s/foldingcurve_umbrella.npy' % str(x)[1::] for x in lam]
    Q_files[-3] = '/home/edz3fz/proteinmontecarlo/results/1PGB/surface/lambda.6/foldingcurve.npy' 
    Q_files[-2] = '/home/edz3fz/proteinmontecarlo/results/1PGB/surface/lambda.65/foldingcurve.npy' 
    Q_files[-1] = '/home/edz3fz/proteinmontecarlo/results/1PGB/surface/lambda.7/foldingcurve.npy' 
    Cv_files = ['/home/edz3fz/proteinmontecarlo/results/1PGB/surface/umbrella_lambda%s/heatcap_umbrella.npy' % str(x)[1::] for x in lam]
    Cv_files[-2] = '/home/edz3fz/proteinmontecarlo/results/1PGB/surface/lambda.65/heatcap.npy' 
    Cv_files[-1] = '/home/edz3fz/proteinmontecarlo/results/1PGB/surface/lambda.7/heatcap.npy' 
    colors = cm.cool(numpy.linspace(0,1,len(lam)))
    
    f = plt.figure(1,(7,8))
    plt.rc('text',usetex=True)
    matplotlib.rc('font', family = 'serif',size=20)
    font = {'family' : 'serif',
            'size'   : 20}
    ax1 = plt.subplot(211)
    for i in range(len(lam)):
        data = numpy.load(Q_files[i])
        if i < 10:
            x=30
            ax1.errorbar(data[0,-x::],data[1,-x::],data[2,-x::],label=r'$\lambda$ = %s' % lam[i], color=colors[i])
        else:
            ax1.errorbar(data[0,:],data[1,:],data[2,:],label=r'$\lambda$ = %s' % lam[i], color=colors[i])
    soln = '/home/edz3fz/proteinmontecarlo/results/1PGB/solution/foldingcurve.npy'
    data = numpy.load(soln)
    ax1.errorbar(data[0,:],data[1,:],data[2,:],label='solution', color='k')
    plt.ylabel('Q')
    plt.setp(ax1.get_xticklabels(), visible = False)
    plt.legend(bbox_to_anchor=(1.37,.5),prop={'size':12})
    plt.xlim((200,400))

    ax2 = plt.subplot(212)
    for i in range(len(lam)):
        data = numpy.load(Cv_files[i])
        if i < 11:
            x=30
            ax2.errorbar(data[0,-x::],data[1,-x::],data[2,-x::],label=r'$\lambda$ = %s' % lam[i], color=colors[i])
        else:
            ax2.errorbar(data[0,:],data[1,:],data[2,:],label=r'$\lambda$ = %s' % lam[i], color=colors[i])
    soln = '/home/edz3fz/proteinmontecarlo/results/1PGB/solution/heatcap.npy'
    data = numpy.load(soln)
    ax2.errorbar(data[0,:],data[1,:],data[2,:],label='solution', color='k')
    #plt.ylabel(r'$C_{v}  \textnormal{ (kcal/mol$\cdot$K)}$')
    f.text(.06,.3,r'$C_{v}  \textnormal{ (kcal/mol$\cdot$K)}$',ha='center',va='center',rotation='vertical')
    plt.xlabel('temperature (K)')
    #plt.legend(prop={'size':8})
    plt.xlim((200,400))
    plt.yticks(numpy.arange(0,4.5,.5))

    f.subplots_adjust(hspace=0, right=.75, left=.15)
    plt.savefig('/home/edz3fz/proteinmontecarlo/manuscripts/figures/Fig6_foldingcurve.eps')
    plt.show()
 
if __name__ == '__main__':
    main()
