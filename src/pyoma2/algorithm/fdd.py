"""
FREQUENCY DOMAIN DECOMPOSITION (FDD) ALGORITHM MODULE

This module provides implementation of the Frequency Domain Decomposition (FDD) and Enhanced
Frequency Domain Decomposition (EFDD) algorithms, along with their adaptations for multi-setup
experimental data. These algorithms are essential for operational modal analysis in structural
dynamics, where they are used to identify modal parameters such as natural frequencies, damping
ratios, and mode shapes from ambient vibration measurements.

Classes:
    FDD_algo : Implements the basic FDD algorithm for single setup modal analysis.
    EFDD_algo : Extends FDD_algo to provide Enhanced FDD analysis.
    FSDD_algo : Implements the Frequency-Spatial Domain Decomposition, a variant of EFDD.
    FDD_algo_MS : Adapts FDD_algo for multi-setup modal analysis.
    EFDD_algo_MS : Extends EFDD_algo for multi-setup scenarios.

Each class contains methods for executing the respective algorithms, extracting modal parameters,
and plotting results. The module also includes utility functions and classes for visualization
and interactive analysis.

Notes:
    - This module is part of the pyoma2 package, designed for advanced modal analysis and
    system identification.
    - Users should be familiar with the concepts of modal analysis and system identification to
    effectively use this module.

References:
    .. [1] Brincker, R., Zhang, L., & Andersen, P. (2001). Modal identification of output-only
        systems using frequency domain decomposition. Smart Materials and Structures, 10(3), 441.

    .. [2] Brincker, R., Ventura, C. E., & Andersen, P. (2001). Damping estimation by frequency
        domain decomposition. In Proceedings of IMAC 19: A Conference on Structural Dynamics,
        February 5-8, 2001, Hyatt Orlando, Kissimmee, Florida. Society for Experimental Mechanics.

    .. [3] Zhang, L., Wang, T., & Tamura, Y. (2010). A frequency–spatial domain decomposition
        (FSDD) method for operational modal analysis. Mechanical Systems and Signal Processing,
        24(5), 1227-1239.
"""
from __future__ import annotations

import logging
import typing

import matplotlib.pyplot as plt
import pandas as pd

from pyoma2.algorithm.base import BaseAlgorithm
from pyoma2.algorithm.data.geometry import Geometry1, Geometry2
from pyoma2.algorithm.data.result import (
    EFDDResult,
    FDDResult,
)
from pyoma2.algorithm.data.run_params import (
    EFDDRunParams,
    FDDRunParams,
)
from pyoma2.functions import (
    FDD_funct,
    plot_funct,
)
from pyoma2.functions.plot_funct import (
    plt_lines,
    plt_nodes,
    plt_quiver,
    plt_surf,
    set_ax_options,
    set_view,
)
from pyoma2.plot.anim_mode import AniMode
from pyoma2.plot.Sel_from_plot import SelFromPlot

logger = logging.getLogger(__name__)


# =============================================================================
# SINGLE SETUP
# =============================================================================
# FREQUENCY DOMAIN DECOMPOSITION
# FIXME ADD REFERENCES
class FDD_algo(BaseAlgorithm[FDDRunParams, FDDResult, typing.Iterable[float]]):
    """
    Frequency Domain Decomposition (FDD) algorithm for operational modal analysis [1]_.

    This class implements the FDD algorithm, used to identify modal parameters such as
    natural frequencies, damping ratios, and mode shapes from ambient vibrations. The algorithm
    operates in the frequency domain and is suitable for output-only modal analysis.

    Attributes
    ----------
    RunParamCls : Type[FDDRunParams]
        Class of the run parameters specific to the FDD algorithm.
    ResultCls : Type[FDDResult]
        Class of the results generated by the FDD algorithm.
    data : Iterable[float]
        Input data for the algorithm, typically a time series of vibration measurements.

    Methods
    -------
    run() -> FDDResult
        Executes the FDD algorithm and returns frequency domain decomposition results.
    mpe(...)
        Performs Modal Parameter Estimation (MPE) on selected frequencies.
    mpe_fromPlot(...)
        Interactive MPE using a plot to select frequencies.
    plot_CMIF(...)
        Plots the Complex Mode Indication Function (CMIF).
    plot_mode_g1(...)
        Plots mode shapes for a given mode number using Geometry1.
    plot_mode_g2(...)
        Plots mode shapes for a given mode number using Geometry2.
    anim_mode_g2(...)
        Animates mode shapes for a given mode number using Geometry2.

    References
    ----------
    .. [1] Brincker, R., Zhang, L., & Andersen, P. (2001). Modal identification of output-only
        systems using frequency domain decomposition. Smart Materials and Structures, 10(3), 441.
    """

    RunParamCls = FDDRunParams
    ResultCls = FDDResult

    def run(self) -> FDDResult:
        """
        Executes the FDD algorithm on the input data and computes modal parameters.

        Processes the input time series data to compute the spectral density matrix. It then
        extracts its singular values and vectors, which are crucial for modal parameter identification.

        Returns
        -------
        FDDResult
            An object containing frequency spectrum, spectral density matrix, singular values,
            and vectors as analysis results.
        """
        super()._pre_run()
        Y = self.data.T
        nxseg = self.run_params.nxseg
        method = self.run_params.method_SD
        pov = self.run_params.pov
        # self.run_params.df = 1 / dt / nxseg

        freq, Sy = FDD_funct.SD_Est(Y, Y, self.dt, nxseg, method=method, pov=pov)
        Sval, Svec = FDD_funct.SD_svalsvec(Sy)

        # Return results
        return self.ResultCls(
            freq=freq,
            Sy=Sy,
            S_val=Sval,
            S_vec=Svec,
        )

    def mpe(self, sel_freq: typing.List[float], DF: float = 0.1) -> typing.Any:
        """
        Performs Modal Parameter Estimation (MPE) on selected frequencies using FDD results.

        Estimates modal parameters such as natural frequencies and mode shapes from the
        frequencies specified by the user.

        Parameters
        ----------
        sel_freq : List[float]
            List of selected frequencies for modal parameter estimation.
        DF : float, optional
            Frequency resolution for estimation. Default is 0.1.

        Returns
        -------
        None
            The method updates the results in the associated FDDResult object with the estimated
            modal parameters.
        """
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

    def mpe_fromPlot(
        self, freqlim: typing.Optional[tuple[float, float]] = None, DF: float = 0.1
    ) -> typing.Any:
        """
        Extracts modal parameters interactively from a plot using selected frequencies.

        This method allows for interactive selection of frequencies from a plot, followed by
        MPE at those frequencies.

        Parameters
        ----------
        freqlim : Optional[tuple[float, float]], optional
            Frequency range for the interactive plot. Default is None.
        DF : float, optional
            Frequency resolution for estimation. Default is 0.1.

        Returns
        -------
        None
            Updates the results in the associated FDDResult object with the selected modal parameters.
        """
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

    def plot_CMIF(
        self,
        freqlim: typing.Optional[tuple[float, float]] = None,
        nSv: typing.Optional[int] = "all",
    ) -> typing.Any:
        """
        Plots the Complex Mode Indication Function (CMIF) for the FDD results.

        CMIF is used to identify modes in the frequency domain data. It plots the singular values
        of the spectral density matrix as a function of frequency.

        Parameters
        ----------
        freqlim : Optional[tuple[float, float]], optional
            Frequency range for the CMIF plot. Default is None.
        nSv : Optional[int], optional
            Number of singular values to include in the plot. Default is 'all'.

        Returns
        -------
        matplotlib.figure.Figure
            The figure object containing the CMIF plot.
        """
        if not self.result:
            raise ValueError("Run algorithm first")
        fig, ax = plot_funct.CMIF_plot(
            S_val=self.result.S_val, freq=self.result.freq, freqlim=freqlim, nSv=nSv
        )
        return fig, ax

    def plot_mode_g1(
        self,
        Geo1: Geometry1,
        mode_numb: int,
        scaleF: int = 1,
        view: typing.Literal["3D", "xy", "xz", "yz", "x", "y", "z"] = "3D",
        remove_fill: bool = True,
        remove_grid: bool = True,
        remove_axis: bool = True,
    ) -> typing.Any:
        """
        Plots mode shapes for a specified mode number using the Geometry1 setup.

        Visualizes the mode shapes determined by the FDD analysis in a 3D space, using the
        geometry provided by Geometry1.

        Parameters
        ----------
        Geo1 : Geometry1
            The Geometry1 object containing sensor locations and directions.
        mode_numb : int
            The mode number to visualize.
        scaleF : int, optional
            Scale factor for the mode shape visualization. Default is 1.
        view : {'3D', 'xy', 'xz', 'yz', 'x', 'y', 'z'}, optional
            The viewpoint for the 3D plot. Default is '3D'.
        remove_fill, remove_grid, remove_axis : bool, optional
            Options to customize the appearance of the plot.

        Returns
        -------
        matplotlib.figure.Figure
            The figure object containing the mode shape plot.
        """

        if self.result.Fn is None:
            raise ValueError("Run algorithm first")

        # Select the (real) mode shape
        phi = self.result.Phi[:, int(mode_numb - 1)].real
        fn = self.result.Fn[int(mode_numb - 1)]

        fig = plt.figure(figsize=(8, 8), tight_layout=True)
        ax = fig.add_subplot(111, projection="3d")

        # set title
        ax.set_title(f"Mode nr. {mode_numb}, $f_n$={fn:.3f}Hz")

        # plot sensors' nodes
        sens_coord = Geo1.sens_coord[["x", "y", "z"]].to_numpy()
        plt_nodes(ax, sens_coord, color="red")

        # plot Mode shape
        plt_quiver(
            ax,
            sens_coord,
            Geo1.sens_dir * phi.reshape(-1, 1),
            scaleF=scaleF,
            #            names=Geo1.sens_names,
        )

        # Check that BG nodes are defined
        if Geo1.bg_nodes is not None:
            # if True plot
            plt_nodes(ax, Geo1.bg_nodes, color="gray", alpha=0.5)
            # Check that BG lines are defined
            if Geo1.bg_lines is not None:
                # if True plot
                plt_lines(ax, Geo1.bg_nodes, Geo1.bg_lines, color="gray", alpha=0.5)
            if Geo1.bg_surf is not None:
                # if True plot
                plt_surf(ax, Geo1.bg_nodes, Geo1.bg_surf, alpha=0.1)

        # check for sens_lines
        if Geo1.sens_lines is not None:
            # if True plot
            plt_lines(ax, sens_coord, Geo1.sens_lines, color="red")

        # Set ax options
        set_ax_options(
            ax,
            bg_color="w",
            remove_fill=remove_fill,
            remove_grid=remove_grid,
            remove_axis=remove_axis,
        )

        # Set view
        set_view(ax, view=view)
        return fig, ax

    def plot_mode_g2(
        self,
        Geo2: Geometry2,
        mode_numb: typing.Optional[int],
        scaleF: int = 1,
        view: typing.Literal["3D", "xy", "xz", "yz", "x", "y", "z"] = "3D",
        remove_fill: bool = True,
        remove_grid: bool = True,
        remove_axis: bool = True,
        *args,
        **kwargs,
    ) -> typing.Any:
        """
        Plots mode shapes for a specified mode number using the Geometry2 setup.

        Visualizes mode shapes determined by the FDD analysis using Geometry2, which can include
        more complex structures and sensor arrangements compared to Geometry1.

        Parameters
        ----------
        Geo2 : Geometry2
            The Geometry2 object containing detailed sensor and structure information.
        mode_numb : Optional[int]
            The mode number to visualize. If None, all modes are plotted.
        scaleF : int, optional
            Scale factor for the mode shape visualization. Default is 1.
        view, remove_fill, remove_grid, remove_axis : optional
            Additional parameters for plot customization.

        Returns
        -------
        matplotlib.figure.Figure
            The figure object showing the mode shape.
        """
        if self.result.Fn is None:
            raise ValueError("Run algorithm first")

        # Select the (real) mode shape
        fn = self.result.Fn[int(mode_numb - 1)]
        phi = self.result.Phi[:, int(mode_numb - 1)].real * scaleF
        # create mode shape dataframe
        df_phi = pd.DataFrame(
            {"sName": Geo2.sens_names, "Phi": phi},
        )
        mapping = dict(zip(df_phi["sName"], df_phi["Phi"]))
        # reshape the mode shape dataframe to fit the pts coord
        df_phi_map = Geo2.sens_map.replace(mapping).astype(float)
        # add together coordinates and mode shape displacement
        newpoints = Geo2.pts_coord.add(df_phi_map * Geo2.sens_sign, fill_value=0)
        # extract only the displacement array
        newpoints = newpoints.to_numpy()[:, 1:]

        # create fig and ax
        fig = plt.figure(figsize=(8, 8), tight_layout=True)
        ax = fig.add_subplot(111, projection="3d")

        # set title
        ax.set_title(f"Mode nr. {mode_numb}, $f_n$={fn:.3f}Hz")

        # Check that BG nodes are defined
        if Geo2.bg_nodes is not None:
            # if True plot
            plot_funct.plt_nodes(ax, Geo2.bg_nodes, color="gray", alpha=0.5)
            # Check that BG lines are defined
            if Geo2.bg_lines is not None:
                # if True plot
                plot_funct.plt_lines(
                    ax, Geo2.bg_nodes, Geo2.bg_lines, color="gray", alpha=0.5
                )
            if Geo2.bg_surf is not None:
                # if True plot
                plot_funct.plt_surf(ax, Geo2.bg_nodes, Geo2.bg_surf, alpha=0.1)
        # PLOT MODE SHAPE
        plot_funct.plt_nodes(ax, newpoints, color="red")
        # check for sens_lines
        if Geo2.sens_lines is not None:
            # if True plot
            plot_funct.plt_lines(ax, newpoints, Geo2.sens_lines, color="red")

        # Set ax options
        plot_funct.set_ax_options(
            ax,
            bg_color="w",
            remove_fill=remove_fill,
            remove_grid=remove_grid,
            remove_axis=remove_axis,
        )

        # Set view
        plot_funct.set_view(ax, view=view)

        return fig, ax

    def anim_mode_g2(
        self,
        Geo2: Geometry2,
        mode_numb: typing.Optional[int],
        scaleF: int = 1,
        view: typing.Literal["3D", "xy", "xz", "yz", "x", "y", "z"] = "3D",
        remove_fill: bool = True,
        remove_grid: bool = True,
        remove_axis: bool = True,
        saveGIF: bool = False,
        *args,
        **kwargs,
    ) -> typing.Any:
        """
        Creates an animation of mode shapes for a specified mode number using Geometry2.

        Animates the mode shapes in a 3D environment, providing a dynamic visualization
        of the modal behavior of the structure as per the Geometry2 setup.

        Parameters
        ----------
        Geo2 : Geometry2
            Geometry2 setup object for the animation.
        mode_numb : Optional[int]
            Mode number to animate. If None, default behavior is applied.
        scaleF : int, optional
            Scale factor for mode shape visualization. Default is 1.
        view, remove_fill, remove_grid, remove_axis, saveGIF : optional
            Parameters for animation customization.

        Returns
        -------
        None
            Initiates and displays an animation of the mode shapes.
        """
        if self.result.Fn is None:
            raise ValueError("Run algorithm first")

        Res = self.result
        logger.debug("Running Anim Mode FDD")
        AniMode(
            Geo=Geo2,
            Res=Res,
            mode_numb=mode_numb,
            scaleF=scaleF,
            view=view,
            remove_axis=remove_axis,
            remove_fill=remove_fill,
            remove_grid=remove_grid,
            saveGIF=saveGIF,
        )
        logger.debug("...end AniMode FDD...")


# ------------------------------------------------------------------------------
# ENHANCED FREQUENCY DOMAIN DECOMPOSITION EFDD
# FIXME ADD REFERENCE
class EFDD_algo(FDD_algo[EFDDRunParams, EFDDResult, typing.Iterable[float]]):
    """
    Enhanced Frequency Domain Decomposition (EFDD) Algorithm Class [2]_.

    This class implements the EFDD algorithm, an enhanced version of the basic FDD method.
    It provides more accurate modal parameters from ambient vibration data.

    Attributes
    ----------
    method : typing.Literal["EFDD", "FSDD"]
        Specifies the method type used in the analysis. Set to "EFDD" for this class.
    RunParamCls : EFDDRunParams
        Class for the run parameters specific to the EFDD algorithm.
    ResultCls : EFDDResult
        Class for storing results obtained from the EFDD analysis.

    Methods
    -------
    mpe(...)
        Executes Modal Parameter Estimation (MPE) for selected frequencies.
    mpe_fromPlot(...)
        Interactive MPE using plots for selecting frequencies in EFDD analysis.
    plot_FIT(...)
        Generates a Frequency domain Identification (FIT) plot for visualizing EFDD results.

    References
    ----------
    .. [2] Brincker, R., Ventura, C. E., & Andersen, P. (2001). Damping estimation by frequency
        domain decomposition. In Proceedings of IMAC 19: A Conference on Structural Dynamics,
        February 5-8, 2001, Hyatt Orlando, Kissimmee, Florida. Society for Experimental Mechanics.

    Notes
    -----
    - Inherits from `FDD_algo` and provides specialized methods and functionalities
    for EFDD-specific analyses.
    """

    method: typing.Literal["EFDD", "FSDD"] = "EFDD"

    RunParamCls = EFDDRunParams
    ResultCls = EFDDResult

    def mpe(
        self,
        sel_freq: typing.List[float],
        DF1: float = 0.1,
        DF2: float = 1.0,
        cm: int = 1,
        MAClim: float = 0.85,
        sppk: int = 3,
        npmax: int = 20,
    ) -> typing.Any:
        """
        Performs Modal Parameter Estimation (MPE) on selected frequencies using EFDD results.

        Estimates modal parameters such as natural frequencies, damping ratios, and mode shapes
        from the frequencies specified by the user.

        Parameters
        ----------
        sel_freq : List[float]
            List of selected frequencies for modal parameter estimation.
        DF1 : float, optional
            Frequency resolution for the first stage of EFDD. Default is 0.1.
        DF2 : float, optional
            Frequency resolution for the second stage of EFDD. Default is 1.0.
        cm : int, optional
            Number of closely spaced modes. Default is 1.
        MAClim : float, optional
            Minimum acceptable Modal Assurance Criterion value. Default is 0.85.
        sppk : int, optional
            Number of peaks to skip for the fit. Default is 3.
        npmax : int, optional
            Maximum number of peaks to use in the fit. Default is 20.

        Returns
        -------
        None
            Updates the EFDDResult object with estimated modal parameters.
        """

        # Save run parameters
        self.run_params.sel_freq = sel_freq
        self.run_params.DF1 = DF1
        self.run_params.DF2 = DF2
        self.run_params.cm = cm
        self.run_params.MAClim = MAClim
        self.run_params.sppk = sppk
        self.run_params.npmax = npmax

        # Extract modal results
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

    def mpe_fromPlot(
        self,
        DF1: float = 0.1,
        DF2: float = 1.0,
        cm: int = 1,
        MAClim: float = 0.85,
        sppk: int = 3,
        npmax: int = 20,
        freqlim: typing.Optional[tuple[float, float]] = None,
    ) -> typing.Any:
        """
        Performs Interactive Modal Parameter Estimation using plots in EFDD analysis.

        Allows interactive selection of frequencies from a plot for modal parameter estimation.
        The method enhances user interaction and accuracy in selecting the frequencies for analysis.

        Parameters
        ----------
        DF1 : float, optional
            Frequency resolution for the first stage of EFDD. Default is 0.1.
        DF2 : float, optional
            Frequency resolution for the second stage of EFDD. Default is 1.0.
        cm : int, optional
            Number of clusters for mode separation. Default is 1.
        MAClim : float, optional
            Minimum acceptable MAC value. Default is 0.85.
        sppk : int, optional
            Number of spectral peaks to consider. Default is 3.
        npmax : int, optional
            Maximum number of peaks. Default is 20.
        freqlim : Optional[tuple[float, float]], optional
            Frequency limit for interactive plot. Default is None.

        Returns
        -------
        None
            Updates the EFDDResult object with modal parameters selected from the plot.
        """

        # Save run parameters
        self.run_params.DF1 = DF1
        self.run_params.DF2 = DF2
        self.run_params.cm = cm
        self.run_params.MAClim = MAClim
        self.run_params.sppk = sppk
        self.run_params.npmax = npmax

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

    def plot_FIT(
        self, freqlim: typing.Optional[tuple[float, float]] = None, *args, **kwargs
    ) -> typing.Any:
        """
        Plots Frequency domain Identification (FIT) results for EFDD analysis.

        Generates a FIT plot to visualize the quality and accuracy of modal identification in EFDD.

        Parameters
        ----------
        freqlim : Optional[tuple[float, float]], optional
            Frequency limit for the FIT plot. Default is None.
        *args, **kwargs
            Additional arguments and keyword arguments for plot customization.

        Returns
        -------
        matplotlib.figure.Figure
            The figure object containing the FIT plot.
        """

        if not self.result:
            raise ValueError("Run algorithm first")

        fig, ax = plot_funct.EFDD_FIT_plot(
            Fn=self.result.Fn,
            Xi=self.result.Xi,
            PerPlot=self.result.forPlot,
            freqlim=freqlim,
        )
        return fig, ax


# ------------------------------------------------------------------------------
# FREQUENCY SPATIAL DOMAIN DECOMPOSITION FSDD
# FIXME ADD REFERENCE
class FSDD_algo(EFDD_algo):
    """
    Frequency-Spatial Domain Decomposition (FSDD) Algorithm Class [3]_.

    This class provides the implementation of the Frequency-Spatial Domain Decomposition (FSDD)
    algorithm, a variant of the Enhanced Frequency Domain Decomposition (EFDD) method.
    The FSDD approach extends the capabilities of EFDD enhancing the accuracy of modal parameter
    estimation in operational modal analysis.

    Attributes
    ----------
    method : "FSDD"
        The method type used in the analysis, set to "FSDD" for this class.
    RunParamCls : Type[EFDDRunParams]
        Class for specifying run parameters unique to the FSDD algorithm.
    ResultCls : Type[EFDDResult]
        Class for storing results obtained from the FSDD analysis.

    Methods
    -------
    Inherits all methods from the EFDD_algo class, with modifications for the FSDD approach.

    References
    ----------
    .. [3] Zhang, L., Wang, T., & Tamura, Y. (2010). A frequency–spatial domain decomposition
        (FSDD) method for operational modal analysis. Mechanical Systems and Signal Processing,
        24(5), 1227-1239.

    Notes
    -----
    Inherits functionalities from the EFDD_algo class while focusing on the unique
    aspects of the FSDD approach for more refined modal analysis.
    """

    method: str = "FSDD"


# =============================================================================
# MULTI SETUP
# =============================================================================
# FREQUENCY DOMAIN DECOMPOSITION
class FDD_algo_MS(FDD_algo[FDDRunParams, FDDResult, typing.Iterable[dict]]):
    """
    Frequency Domain Decomposition (FDD) Algorithm for Multi-Setup Analysis.

    This class extends the standard FDD algorithm to handle data from multiple experimental setups.
    It's designed to merge and analyze data from different configurations.

    Attributes
    ----------
    RunParamCls : Type[FDDRunParams]
        Defines the run parameters specific to the FDD algorithm for multi-setup analysis.
    ResultCls : Type[FDDResult]
        Represents the class for storing results obtained from multi-setup FDD analysis.
    data : Iterable[dict]
        The input data for the algorithm, typically a collection of vibration measurements
        from multiple setups.

    Methods
    -------
    run() -> FDDResult
        Conducts the FDD analysis on multi-setup data, producing spectral density matrices,
        singular values, and vectors as results.

    Notes
    -----
    Inherits the functionality from the standard FDD algorithm class, modifying and extending it
    for application to datasets derived from multiple experimental setups.
    """

    RunParamCls = FDDRunParams
    ResultCls = FDDResult

    def run(self) -> FDDResult:
        """
        Executes the FDD algorithm on multi-setup data for operational modal analysis.

        Processes input data from multiple experimental setups to conduct frequency domain decomposition.
        The method computes spectral density matrices for each setup and then merges them to extract
        singular values and vectors.

        Returns
        -------
        FDDResult
            An object encapsulating the results of the FDD analysis for multi-setup data, including
            frequency spectrum, merged spectral density matrix, and associated singular values and vectors.
        """

        super()._pre_run()
        Y = self.data
        nxseg = self.run_params.nxseg
        method = self.run_params.method_SD
        pov = self.run_params.pov
        # self.run_params.df = 1 / dt / nxseg

        freq, Sy = FDD_funct.SD_PreGER(Y, self.fs, nxseg=nxseg, method=method, pov=pov)
        Sval, Svec = FDD_funct.SD_svalsvec(Sy)

        # Return results
        return self.ResultCls(
            freq=freq,
            Sy=Sy,
            S_val=Sval,
            S_vec=Svec,
        )


# ------------------------------------------------------------------------------
# ENHANCED FREQUENCY DOMAIN DECOMPOSITION EFDD
class EFDD_algo_MS(EFDD_algo[EFDDRunParams, EFDDResult, typing.Iterable[dict]]):
    """
    Enhanced Frequency Domain Decomposition (EFDD) Algorithm for Multi-Setup Analysis.

    This class extends the EFDD algorithm to accommodate operational modal analysis
    across multiple experimental setups.

    Attributes
    ----------
    method : str
        The EFDD method employed for multi-setup analysis.
    RunParamCls : EFDDRunParams
        Class for specifying run parameters unique to the EFDD algorithm for multi-setups.
    ResultCls : EFDDResult
        Class for storing results obtained from the multi-setup EFDD analysis.
    data : Iterable[dict]
        The input data, consisting of vibration measurements from multiple setups.

    Methods
    -------
    run() -> EFDDResult
        Conducts the EFDD algorithm on multi-setup data, yielding the modal parameters
        such as natural frequencies, damping ratios, and mode shapes.

    Notes
    -----
    This class adapts and enhances the standard EFDD algorithm's functionality for datasets
    derived from multiple experimental setups.
    """

    method = "EFDD"
    RunParamCls = EFDDRunParams
    ResultCls = EFDDResult

    def run(self) -> FDDResult:
        """
        Executes the Enhanced Frequency Domain Decomposition (EFDD) algorithm on multi-setup data.

        Processes input data from multiple experimental setups for operational modal analysis using the EFDD
        method. The method computes spectral density matrices for each setup and then merges them to extract
        singular values and vectors.

        Returns
        -------
        EFDDResult
            An object encapsulating the results of the EFDD analysis for multi-setup data, including enhanced
            frequency spectrum, merged spectral density matrices, and associated singular values and vectors.
        """

        super()._pre_run()
        Y = self.data
        nxseg = self.run_params.nxseg
        method = self.run_params.method_SD
        pov = self.run_params.pov
        # self.run_params.df = 1 / dt / nxseg

        freq, Sy = FDD_funct.SD_PreGER(Y, self.fs, nxseg=nxseg, method=method, pov=pov)
        Sval, Svec = FDD_funct.SD_svalsvec(Sy)

        # Return results
        return self.ResultCls(
            freq=freq,
            Sy=Sy,
            S_val=Sval,
            S_vec=Svec,
        )
