"""FREQUENCY DOMAIN DECOMPOSITION (FDD) ALGORITHM"""

import typing

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from pydantic import (  # controlla che i parametri passati siano quelli giusti
    validate_call,
)
from pyoma2.algorithm.data.result import (
    FDDResult, EFDDResult,
)
from pyoma2.algorithm.data.run_params import (
    FDDRunParams, EFDDRunParams,
)
from pyoma2.functions import (  # noqa: F401
    FDD_funct,
    Gen_funct,
    SSI_funct,
    plot_funct,
    pLSCF_funct,
)
from pyoma2.functions.plot_funct import( 
plt_nodes,plt_lines,plt_quiver,plt_surf,set_ax_options,set_view)

from pyoma2.plot.Sel_from_plot import SelFromPlot
from pyoma2.algorithm.base import BaseAlgorithm
from pyoma2.algorithm.data.geometry import Geometry1, Geometry2
from pyoma2.plot.anim_mode import AniMode

# =============================================================================
# FREQUENCY DOMAIN DECOMPOSITION
class FDD_algo(BaseAlgorithm[FDDRunParams, FDDResult]):
    RunParamCls = FDDRunParams
    ResultCls = FDDResult

    def run(self) -> FDDResult:
        super()._pre_run()
        print(self.run_params)
        Y = self.data.T
        nxseg = self.run_params.nxseg
        method = self.run_params.method_SD
        # self.run_params.df = 1 / dt / nxseg

        freq, Sy = FDD_funct.SD_Est(Y, Y, self.dt, nxseg, method=method)
        Sval, Svec = FDD_funct.SD_svalsvec(Sy)

        # Return results
        return self.ResultCls(
            freq=freq,
            Sy=Sy,
            S_val=Sval,
            S_vec=Svec,
        )

    @validate_call
    def mpe(self, sel_freq: float, DF: float = 0.1) -> typing.Any:
        super().mpe(sel_freq=sel_freq, DF=DF)

        self.run_params.sel_freq = sel_freq
        self.run_params.DF = DF
        Sy = self.result.Sy
        freq = self.result.freq

        # Get Modal Parameters
        Fn_FDD, Phi_FDD = FDD_funct.FDD_MPE(Sy, freq, sel_freq, DF=DF)

        # Save results
        self.result.Fn = Fn_FDD
        self.result.Phi = Phi_FDD

    @validate_call
    def mpe_fromPlot(
        self, freqlim: typing.Optional[float] = None, DF: float = 0.1
    ) -> typing.Any:
        super().mpe_fromPlot(freqlim=freqlim)

        Sy = self.result.Sy
        freq = self.result.freq

        self.run_params.DF = DF

        # chiamare plot interattivo
        SFP = SelFromPlot(algo=self, freqlim=freqlim, plot="FDD")
        sel_freq = SFP.result[0]

        # e poi estrarre risultati
        Fn_FDD, Phi_FDD = FDD_funct.FDD_MPE(Sy, freq, sel_freq, DF=DF)

        # Save results
        self.result.Fn = Fn_FDD
        self.result.Phi = Phi_FDD

    def plot_CMIF(self, 
                  freqlim: typing.Optional[float] = None,
                  nSv: typing.Optional[int] = "all",
                  ) -> typing.Any:
        """Tobe implemented, plot for FDD, EFDD, FSDD
        Mode Identification Function (MIF)
        """
        if not self.result:
            raise ValueError("Run algorithm first")
        fig, ax = plot_funct.CMIF_plot(
            S_val=self.result.S_val,
            freq=self.result.freq,
            freqlim=freqlim,
            nSv=nSv
        )
        return fig, ax

    def plot_mode_g1(self,
                     Geo1: Geometry1,
                     mode_numb : int,
                     scaleF: int = 1,
                     view: typing.Literal["3D","xy","xz","yz","x","y","z"] = "3D",
                     remove_fill: True | False =True, 
                     remove_grid: True | False =True, 
                     remove_axis: True | False =True
                     ) -> typing.Any:
        """Tobe implemented, plot for FDD, EFDD, FSDD
        Mode Identification Function (MIF)
        """

        if self.result.Fn is None:
            raise ValueError("Run algorithm first")

        # Select the (real) mode shape
        phi = self.result.Phi[:,int(mode_numb-1)].real
        fn = self.result.Fn[int(mode_numb-1)]

        fig = plt.figure(figsize=(10,10),tight_layout=True)
        ax = fig.add_subplot(111, projection='3d')

        # set title
        ax.set_title(f"Mode nr. {mode_numb}, $f_n$={fn:.3f}Hz"
                          )

        # plot sensors' nodes
        sens_coord= Geo1.sens_coord[["x","y","z"]].to_numpy()
        plt_nodes(ax,sens_coord,color="red")

        # plot Mode shape
        plt_quiver(ax,sens_coord,Geo1.sens_dir*phi.reshape(-1,1),
                   scaleF=scaleF,names=Geo1.sens_names)

        # Check that BG nodes are defined
        if Geo1.bg_nodes is not None:
            # if True plot
            plt_nodes(ax,Geo1.bg_nodes,color="gray",alpha=0.5)
            # Check that BG lines are defined
            if Geo1.bg_lines is not None:
                # if True plot
                plt_lines(ax,Geo1.bg_nodes,Geo1.bg_lines,
                      color="gray",alpha=0.5)
            if Geo1.bg_surf is not None:
                # if True plot
                plt_surf(ax,Geo1.bg_nodes,Geo1.bg_surf
                         ,alpha=0.1)

        # check for sens_lines
        if Geo1.sens_lines is not None:
            # if True plot
            plt_lines(ax,sens_coord,Geo1.sens_lines,
                      color="red")

        # Set ax options
        set_ax_options(ax,bg_color="w",
                       remove_fill=remove_fill,
                       remove_grid=remove_grid,
                       remove_axis=remove_axis)

        # Set view
        set_view(ax, view=view)
        return fig, ax


    def plot_mode_g2(self,
                     Geo2: Geometry2,
                     mode_numb: typing.Optional[int],
                     scaleF: int = 1,
                     view:typing.Literal["3D","xy","xz","yz","x","y","z"]="3D",
                     remove_fill: True | False = True, 
                     remove_grid: True | False = True, 
                     remove_axis: True | False = True,
                     *args, **kwargs) -> typing.Any:
        """Tobe implemented, plot for FDD, EFDD, FSDD
        Mode Identification Function (MIF)
        """
        if self.result.Fn is None:
            raise ValueError("Run algorithm first")

        # Select the (real) mode shape
        fn = self.result.Fn[int(mode_numb-1)]
        phi = self.result.Phi[:,int(mode_numb-1)].real*scaleF
        # create mode shape dataframe
        df_phi = pd.DataFrame({
            "sName":Geo2.sens_names,
            "Phi":phi
            },)
        mapping = dict(zip(df_phi['sName'], df_phi['Phi']))
        # reshape the mode shape dataframe to fit the pts coord
        df_phi_map = Geo2.sens_map.replace(mapping).astype(float)
        # add together coordinates and mode shape displacement
        newpoints = Geo2.pts_coord.add(df_phi_map*Geo2.sens_sign, fill_value=0)
        # extract only the displacement array
        newpoints = newpoints.to_numpy()[:,1:]

        # create fig and ax
        fig = plt.figure(figsize=(8,8),tight_layout=True)
        ax = fig.add_subplot(111, projection='3d')
        
        # set title
        ax.set_title(f"Mode nr. {mode_numb}, $f_n$={fn:.3f}Hz"
                          )

        # Check that BG nodes are defined
        if Geo2.bg_nodes is not None:
            # if True plot
            plot_funct.plt_nodes(ax,Geo2.bg_nodes,color="gray",alpha=0.5)
            # Check that BG lines are defined
            if Geo2.bg_lines is not None:
                # if True plot
                plot_funct.plt_lines(ax,Geo2.bg_nodes,Geo2.bg_lines,
                      color="gray",alpha=0.5)
            if Geo2.bg_surf is not None:
                # if True plot
                plot_funct.plt_surf(ax,Geo2.bg_nodes,Geo2.bg_surf
                         ,alpha=0.1)
        # PLOT MODE SHAPE
        plot_funct.plt_nodes(ax,newpoints,color="red")
        # check for sens_lines
        if Geo2.sens_lines is not None:
            # if True plot
            plot_funct.plt_lines(ax,newpoints,Geo2.sens_lines,
                      color="red")

        # Set ax options
        plot_funct.set_ax_options(ax,bg_color="w",
                       remove_fill=remove_fill,
                       remove_grid=remove_grid,
                       remove_axis=remove_axis)

        # Set view
        plot_funct.set_view(ax, view=view)

        return fig, ax

    def anim_mode_g2(self,
                     Geo2: Geometry2,
                     mode_numb: typing.Optional[int],
                     scaleF: int = 1,
                     view: typing.Literal["3D","xy","xz","yz","x","y","z"] = "3D",
                     remove_fill: True | False =True, 
                     remove_grid: True | False =True, 
                     remove_axis: True | False =True,
                     *args, **kwargs) -> typing.Any:
        """Tobe implemented, plot for FDD, EFDD, FSDD
        Mode Identification Function (MIF)
        """
        if self.result.Fn is None:
            raise ValueError("Run algorithm first")
            
        Res = self.result
        AniMode(Geo=Geo2,Res=Res, mode_numb=mode_numb,
                scaleF=scaleF,view=view,remove_axis=remove_axis,
                remove_fill=remove_fill,remove_grid=remove_grid)

# =============================================================================
# ENHANCED FREQUENCY DOMAIN DECOMPOSITION EFDD
class EFDD_algo(FDD_algo[EFDDRunParams, EFDDResult]):
    method: typing.Literal["EFDD", "FSDD"] = "EFDD"

    RunParamCls = EFDDRunParams
    ResultCls = EFDDResult

    @validate_call
    def mpe(
        self,
        sel_freq: float,
        DF1: float = 0.1,
        DF2: float = 1.0,
        cm: int = 1,
        MAClim: float = 0.85,
        sppk: int = 3,
        npmax: int = 20,
    ) -> typing.Any:

        Fn_FDD, Xi_FDD, Phi_FDD, forPlot = FDD_funct.EFDD_MPE(
            self.result.Sy,
            self.result.freq,
            self.dt,
            sel_freq,
            self.run_param.method_SD,
            method=self.method,
            DF1=DF1,
            DF2=DF2,
            cm=cm,
            MAClim=MAClim,
            sppk=sppk,
            npmax=npmax,
        )

        # Save results
        self.result.Fn = Fn_FDD.reshape(-1)
        self.result.Xi = Xi_FDD.reshape(-1)
        self.result.Phi = Phi_FDD
        self.result.forPlot = forPlot

    @validate_call
    def mpe_fromPlot(
        self,
        DF1: float = 0.1,
        DF2: float = 1.0,
        cm: int = 1,
        MAClim: float = 0.85,
        sppk: int = 3,
        npmax: int = 20,
        freqlim: typing.Optional[float] = None,
    ) -> typing.Any:

        # chiamare plot interattivo
        SFP = SelFromPlot(algo=self, freqlim=freqlim, plot="FDD")
        sel_freq = SFP.result[0]

        # e poi estrarre risultati
        Fn_FDD, Xi_FDD, Phi_FDD, forPlot = FDD_funct.EFDD_MPE(
            self.result.Sy,
            self.result.freq,
            self.dt,
            sel_freq,
            self.run_params.method_SD,
            method=self.method,
            DF1=DF1,
            DF2=DF2,
            cm=cm,
            MAClim=MAClim,
            sppk=sppk,
            npmax=npmax,
        )

        # Save results
        self.result.Fn = Fn_FDD.reshape(-1)
        self.result.Xi = Xi_FDD.reshape(-1)
        self.result.Phi = Phi_FDD
        self.result.forPlot = forPlot

    def plot_FIT(self,
                 freqlim: typing.Optional[float] = None,
                 *args, **kwargs) -> typing.Any:
        """Tobe implemented, plot for FDD, EFDD, FSDD
        Mode Identification Function (MIF)
        """
        if not self.result:
            raise ValueError("Run algorithm first")

        fig, ax = plot_funct.EFDD_FIT_plot(
            Fn=self.result.Fn,
            Xi=self.result.Xi,
            PerPlot = self.result.forPlot,
            freqlim=freqlim,
        )
        return fig, ax


# ------------------------------------------------------------------------------
# FREQUENCY SPATIAL DOMAIN DECOMPOSITION FSDD
class FSDD_algo(EFDD_algo):
    method: typing.Literal["EFDD", "FSDD"] = "FSDD"
