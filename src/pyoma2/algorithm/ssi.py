"""STOCHASTIC SUBSPACE IDENTIFICATION (SSI) ALGORITHM"""

import typing

import numpy as np
from pydantic import (  # controlla che i parametri passati siano quelli giusti
    validate_call,
)

from pyoma2.algorithm.data.result import SSIResult

# from .result import BaseResult
from pyoma2.algorithm.data.run_params import SSIRunParams
from pyoma2.functions import (  # noqa: F401
    FDD_funct,
    Gen_funct,
    SSI_funct,
    plot_funct,
    pLSCF_funct,
)

# from .run_params import BaseRunParams
from pyoma2.plot.Sel_from_plot import SelFromPlot

from .base import BaseAlgorithm


# =============================================================================
# (REF)DATA-DRIVEN STOCHASTIC SUBSPACE IDENTIFICATION
class SSIdat_algo(BaseAlgorithm[SSIRunParams, SSIResult]):
    RunParamType = SSIRunParams
    ResultType = SSIResult
    method: typing.Literal["dat"] = "dat"

    def run(self) -> SSIResult:
        super()._pre_run()
        print(self.run_params)
        Y = self.data.T
        br = self.run_params.br
        # method = self.run_params.method_hank
        ordmin = self.run_params.ordmin
        ordmax = self.run_params.ordmax
        step = self.run_params.step
        err_fn = self.run_params.err_fn
        err_xi = self.run_params.err_xi
        err_phi = self.run_params.err_phi
        xi_max = self.run_params.xi_max

        if self.run_params.ref_ind is not None:
            ref_ind = self.run_params.ref_ind
            Yref = Y[ref_ind, :]
        else:
            Yref = Y

        # Build Hankel matrix
        # qui method deve essere uno nell elseif del file SSI_func (vedi 10 01:00)
        H = SSI_funct.BuildHank(Y, Yref, 1 / self.dt, self.fs, method=self.method)
        # Get state matrix and output matrix
        A, C = SSI_funct.SSI_FAST(H, br, ordmax)
        # Get frequency poles (and damping and mode shapes)
        Fn_pol, Sm_pol, Ms_pol = SSI_funct.SSI_funct.SSI_Poles(
            A, C, ordmax, self.dt, step=step
        )
        # Get the labels of the poles
        Lab = SSI_funct.Lab_stab_SSI(
            Fn_pol, Sm_pol, Ms_pol, ordmin, ordmax, step, err_fn, err_xi, err_phi, xi_max
        )
        Lab

        # FIXME Non serve fare così, basta ritornare la classe result, poi saraà SingleSetup a salvarla
        # # Save results <--
        # self.result = FDD
        # self.result.H = H
        # self.result.A = A
        # self.result.C = C
        # self.result.Lab = Lab
        # self.result.Fn_pol = Fn_pol
        # self.result.Sm_pol = Sm_pol
        # self.result.Ms_pol = Ms_pol

        # Fake result: FIXME return real SSIResult
        return SSIResult(
            Fn=np.asarray([10, 20, 30]),
            Phi=np.asarray([0.1, 0.2, 0.3]),
            Fn_poles=np.asarray([10, 20, 30]),
            xi_poles=np.asarray([0.1, 0.2, 0.3]),
            Phi_poles=np.asarray([0.1, 0.2, 0.3]),
            lam_poles=np.asarray([0.1, 0.2, 0.3]),
            Lab=np.asarray([0.1, 0.2, 0.3]),
            Xi=np.asarray([0.1, 0.2, 0.3]),
        )

    @validate_call
    def mpe(
        self,
        sel_freq: float,
        order: str = "find_min",
        deltaf: float = 0.05,
        rtol: float = 1e-2,
    ) -> typing.Any:
        super().mpe(sel_freq=sel_freq, order=order, deltaf=deltaf, rtol=rtol)

        Fn_pol = self.result.Fn_pol
        Sm_pol = self.result.Sm_pol
        Ms_pol = self.result.Ms_pol
        Lab = self.result.Lab

        Fn_SSI, Xi_SSI, Phi_SSI = SSI_funct.SSI_MPE(
            sel_freq, Fn_pol, Sm_pol, Ms_pol, order, Lab=Lab, deltaf=deltaf, rtol=rtol
        )

        # Save results
        # Qui è corretto perchè result esiste dopo che si è fatto il run()
        self.result.Fn = Fn_SSI
        self.result.Sm = Xi_SSI
        self.result.Ms = Phi_SSI

    @validate_call
    def mpe_fromPlot(
        self,
        freqlim: typing.Optional[float] = None,
    ) -> typing.Any:
        super().mpe_fromPlot(
            freqlim=freqlim,
        )

        Fn_pol = self.result.Fn_pol
        Sm_pol = self.result.Sm_pol
        Ms_pol = self.result.Ms_pol

        # chiamare plot interattivo
        sel_freq, order = SelFromPlot(algo=self, freqlim=freqlim, plot="SSI")

        # e poi estrarre risultati
        Fn_SSI, Xi_SSI, Phi_SSI = SSI_funct.SSI_MPE(
            sel_freq, Fn_pol, Sm_pol, Ms_pol, order, Lab=None, deltaf=0.05, rtol=1e-2
        )

        # Save results
        # Qui è corretto perchè result esiste dopo che si è fatto il run()
        self.result.Fn = Fn_SSI
        self.result.Sm = Xi_SSI
        self.result.Ms = Phi_SSI

    def plot_STDiag(self, *args, **kwargs) -> typing.Any:
        """Tobe implemented, plot for SSIdat, SSIcov
        Stability Diagram
        """
        pass


# =============================================================================
# (REF)COVARIANCE-DRIVEN STOCHASTIC SUBSPACE IDENTIFICATION
class SSIcov_algo(SSIdat_algo):
    method: typing.Literal["cov_bias", "cov_matmul", "cov_unb"] = "cov_bias"

    @validate_call
    def mpe(self, sel_freq: float, order: str = "find_min") -> typing.Any:
        super().mpe(sel_freq=sel_freq, order=order)

        Fn_pol = self.result.Fn_pol
        Sm_pol = self.result.Sm_pol
        Ms_pol = self.result.Ms_pol

        Fn_SSI, Xi_SSI, Phi_SSI = SSI_funct.SSI_MPE(
            sel_freq, Fn_pol, Sm_pol, Ms_pol, order, Lab=None, deltaf=0.05, rtol=1e-2
        )

        # Save results
        # Qui è corretto perchè result esiste dopo che si è fatto il run()
        self.result.Fn = Fn_SSI
        self.result.Sm = Xi_SSI
        self.result.Ms = Phi_SSI

    @validate_call
    def mpe_fromPlot(
        self,
        freqlim: typing.Optional[float] = None,
    ) -> typing.Any:
        super().mpe_fromPlot(
            freqlim=freqlim,
        )

        Fn_pol = self.result.Fn_pol
        Sm_pol = self.result.Sm_pol
        Ms_pol = self.result.Ms_pol

        # chiamare plot interattivo
        sel_freq, order = SelFromPlot(algo=self, freqlim=freqlim, plot="SSI")

        # e poi estrarre risultati
        Fn_SSI, Xi_SSI, Phi_SSI = SSI_funct.SSI_MPE(
            sel_freq, Fn_pol, Sm_pol, Ms_pol, order, Lab=None, deltaf=0.05, rtol=1e-2
        )

        # Save results
        # Qui è corretto perchè result esiste dopo che si è fatto il run()
        self.result.Fn = Fn_SSI
        self.result.Sm = Xi_SSI
        self.result.Ms = Phi_SSI


# =============================================================================
# ------------------------------------------------------------------------------


"""...same for other alghorithms"""
