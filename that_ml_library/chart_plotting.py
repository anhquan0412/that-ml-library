# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/03_chart_plotting.ipynb.

# %% ../nbs/03_chart_plotting.ipynb 3
from __future__ import annotations
from .utils import *
from pathlib import Path
import numpy as np
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
from sklearn.model_selection import learning_curve,validation_curve, RandomizedSearchCV, GridSearchCV
import matplotlib.pyplot as plt
from sklearn.inspection import PartialDependenceDisplay, permutation_importance
import pandas as pd
import plotly.express as px
import dtreeviz
from sklearn.tree import export_graphviz
import graphviz
from matplotlib.cm import get_cmap
import plotly.graph_objects as go
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tools.tools import add_constant
import seaborn as sns
import matplotlib
from scipy.stats import chi2_contingency
from yellowbrick.regressor import ResidualsPlot

# %% auto 0
__all__ = ['get_vif', 'get_correlation_by_threshold', 'get_cat_correlation', 'plot_cat_correlation', 'plot_residuals',
           'plot_prediction_distribution', 'plot_learning_curve', 'plot_validation_curve', 'plot_tree_dtreeviz',
           'plot_classification_tree_sklearn', 'plot_feature_importances', 'plot_permutation_importances',
           'params_2D_heatmap', 'params_3D_heatmap', 'pdp_numerical_only', 'pdp_categorical_only', 'plot_ice_pair',
           'plot_confusion_matrix', 'draw_sankey']

# %% ../nbs/03_chart_plotting.ipynb 6
def get_vif(df:pd.DataFrame, # dataframe to plot
            plot_corr=False, # to plot the correlation matrix
            figsize=(10,10) # Matplotlib figsize
           ):
    """
    Perform variance inflation factor calculation, and optionally plot correlation matrix
    
    Note that your dataframe should only have numerical features to perform VIF
    """
    if plot_corr:
        fig,ax = plt.subplots(figsize=(10,10))
        dataplot = sns.heatmap(df.corr(), fmt=f".2f",cmap="YlGnBu", annot=True)  
        plt.show()

    df_const = add_constant(df)    
    vif = pd.Series([variance_inflation_factor(df_const.values, i) 
                    for i in range(df_const.shape[1])], index=df_const.columns)
    return vif

# %% ../nbs/03_chart_plotting.ipynb 11
def get_correlation_by_threshold(df_corr, # Correlation DataFrame
                         min_thres=0.98 # minimum correlation to take
                        ):
    result_dic={}
    for i,c in enumerate(df_corr.columns.tolist()):
        result = df_corr.iloc[:i,i][np.abs(df_corr.iloc[:i,i])>=min_thres].to_dict()
        result = {k:v for (k,v) in result.items() }
        if len(result)==0: continue
#         print(f'{c}: {result}')
        result_dic[c]=result
    return result_dic

# %% ../nbs/03_chart_plotting.ipynb 15
def _cramer_v(var1, var2):
    """
    Cramer’s V measures association between two nominal variables.
    Cramer’s V lies between 0 and 1 (inclusive).
    0 indicates that the two variables are not linked by any relation.
    1 indicates that there exists a strong association between the two variables.
    """
    crosstab = np.array(pd.crosstab(var1, var2))
    chi2 = chi2_contingency(crosstab)[0]
    observation, min_dim = np.sum(crosstab), min(crosstab.shape) - 1
    return np.sqrt((chi2 / observation) / min_dim)

# %% ../nbs/03_chart_plotting.ipynb 16
def get_cat_correlation(df_cat, # DataFrame with categorical features that have been processed
                       ):
    cramer_matrix = []
    cat_cols = df_cat.columns.tolist()
    for c in cat_cols:
        _tmp = []
        for c1 in cat_cols:
            _tmp.append(_cramer_v(df_cat[c],df_cat[c1]))
        cramer_matrix.append(_tmp)
    cramer_df = pd.DataFrame(cramer_matrix,columns=df_cat.columns.values)
    cramer_df.index = df_cat.columns.values
    return cramer_df

# %% ../nbs/03_chart_plotting.ipynb 17
def plot_cat_correlation(df_cat, # DataFrame with categorical features that have been processed
                        figsize=(10,10), # Matplotlib figsize
                        ):
    cramer_df = get_cat_correlation(df_cat)
    fig,ax = plt.subplots(figsize=figsize)
    dataplot = sns.heatmap(cramer_df, fmt=f".3f",cmap="YlGnBu", annot=True)  
    plt.show()

# %% ../nbs/03_chart_plotting.ipynb 28
def plot_residuals(model, # Regression model
                   X_trn, # Training dataframe
                   y_trn, # Training label
                   X_test=None, # Testing dataframe
                   y_test=None, # Testing label
                   qqplot=True, # To whether plot the qqplot
                  ):
    
    # plot residual plot
    visualizer = ResidualsPlot(model, hist=False, qqplot=qqplot)
    visualizer.fit(X_trn, y_trn)
    if not X_test is None:
        visualizer.score(X_test, y_test)
    visualizer.show()

# %% ../nbs/03_chart_plotting.ipynb 37
def plot_prediction_distribution(y_true, # True label numpy array
                                 y_pred, # Prediction numpy array
                                 figsize=(15,5) # Matplotlib figsize
                                ):
    fig,axes = plt.subplots(1,2,figsize=figsize)    
    df_plot1=pd.DataFrame()
    df_plot1['value'] = y_pred
    df_plot1['type'] = 'Predictions'
    df_plot2=pd.DataFrame()
    df_plot2['value'] = y_true
    df_plot2['type'] = 'True values'
    df_plot = pd.concat([df_plot1,df_plot2],axis=0)

    print(f'MSE: {np.mean((y_true-y_pred)**2)}')
    print(f'RMSE: {np.sqrt(np.mean((y_true-y_pred)**2))}')
    print(f"MAE: {np.mean(np.abs(y_true-y_pred))}")

    sns.histplot(df_plot, x="value", hue="type", element="step",ax=axes[0])
    sns.kdeplot(df_plot, x="value", hue="type", ax=axes[1])
    plt.show()

# %% ../nbs/03_chart_plotting.ipynb 43
def plot_learning_curve(
    estimator, # sklearn's classifier
    title, # Title of the chart
    X, # Training features
    y, # Training label
    axes=None, # matplotlib's axes
    ylim=None, # y axis range limit
    cv=None, # sklearn's cross-validation splitting strategy
    n_jobs=-1, # Number of jobs to run in parallel
    scoring=None, # metric
    train_sizes=[0.05, 0.24, 0.43, 0.62, 0.81, 1.], # List of training size portion
    save_fig=False, # To store the chart as png in images directory
    figsize=(20,5), # Matplotlib figsize
    seed=42 # Random seed
):
    if axes is None:
        _, axes = plt.subplots(1, 2, figsize=figsize)

    axes[0].set_title(title)
    if ylim is not None:
        axes[0].set_ylim(*ylim)
    axes[0].set_xlabel("Training examples")
    axes[0].set_ylabel("Score")

    train_sizes, train_scores, test_scores, fit_times, _ = learning_curve(
        estimator,
        X,
        y,
        scoring=scoring,
        cv=cv,
        n_jobs=n_jobs,
        train_sizes=train_sizes,
        return_times=True,
        random_state=seed
    )
    train_scores_mean = np.mean(train_scores, axis=1)
    train_scores_std = np.std(train_scores, axis=1)
    test_scores_mean = np.mean(test_scores, axis=1)
    test_scores_std = np.std(test_scores, axis=1)
    fit_times_mean = np.mean(fit_times, axis=1)
    fit_times_std = np.std(fit_times, axis=1)

    # Plot learning curve
    axes[0].grid()
    axes[0].fill_between(
        train_sizes,
        train_scores_mean - train_scores_std,
        train_scores_mean + train_scores_std,
        alpha=0.1,
        color="r",
    )
    axes[0].fill_between(
        train_sizes,
        test_scores_mean - test_scores_std,
        test_scores_mean + test_scores_std,
        alpha=0.1,
        color="g",
    )
    axes[0].plot(
        train_sizes, train_scores_mean, "o-", color="r", label="Training score"
    )
    axes[0].plot(
        train_sizes, test_scores_mean, "o-", color="g", label="Cross-validation score"
    )
    axes[0].legend(loc="best")

    # Plot n_samples vs fit_times
    axes[1].grid()
    axes[1].plot(train_sizes, fit_times_mean, "o-")
    axes[1].fill_between(
        train_sizes,
        fit_times_mean - fit_times_std,
        fit_times_mean + fit_times_std,
        alpha=0.1,
    )
    axes[1].set_xlabel("Training examples")
    axes[1].set_ylabel("fit_times")
    axes[1].set_title("Scalability of the model")

    plt.grid()
    if save_fig:
        _path = Path('./images')
        create_dir(_path)
        plt.savefig(_path/f'{title}.png')
    return plt

# %% ../nbs/03_chart_plotting.ipynb 46
def plot_validation_curve(
    estimator, # sklearn's classifier
    title, # Title of the chart
    X, # Training features
    y, # Training label
    ylim=None, # y axis range limit
    cv=None, # sklearn's cross-validation splitting strategy
    param_name=None, # Name of model's hyperparameter
    param_range=None, # List containing range of value for param_name
    is_log=False, # To log the value in param_range, for plotting
    n_jobs=-1, # Number of jobs to run in parallel
    scoring=None, # metric
    save_fig=False, # To store the chart as png in images directory    
    figsize=(8,4), # Matplotlib figsize
    fill_between=True, # To add a upper and lower one-std line for train and test curve
    enumerate_x=False # Convert categorical hyperparam to numerical, for x axis
):
    train_scores, test_scores = validation_curve(
            estimator,
            X,
            y,
            param_name=param_name,
            param_range=param_range,
            scoring=scoring,
            n_jobs=n_jobs,
            cv=cv,
            )
    train_scores_mean = np.mean(train_scores, axis=1)
    train_scores_std = np.std(train_scores, axis=1)
    test_scores_mean = np.mean(test_scores, axis=1)
    test_scores_std = np.std(test_scores, axis=1)
    plt.figure(figsize=figsize)
    plt.title(title)
    plt.xlabel(param_name)
    plt.ylabel("Score")
    if is_log:
        plt.semilogx(param_range, train_scores_mean, marker="o",label="Training score", color="r")
        plt.semilogx(param_range, test_scores_mean, marker="o",label="Cross-validation score", color="g")

    else:
        tmp = param_range
        if enumerate_x:
            tmp = np.arange(1,len(tmp)+1)
        plt.plot(tmp, train_scores_mean, "o-", color="r", label="Training score")
        plt.plot(tmp, test_scores_mean, "o-", color="g", label="Cross-validation score")

    if fill_between:
        plt.fill_between(
            param_range,
            train_scores_mean - train_scores_std,
            train_scores_mean + train_scores_std,
            alpha=0.1,
            color="r",
        )
        plt.fill_between(
            param_range,
            test_scores_mean - test_scores_std,
            test_scores_mean + test_scores_std,
            alpha=0.1,
            color="g",
        )
    if ylim is not None:
        plt.ylim(*ylim)
    plt.grid()
    plt.legend(loc="best")
    if save_fig:
        _path = Path('./images')
        create_dir(_path)
        plt.savefig(_path/f'{title}.png')
    return plt

# %% ../nbs/03_chart_plotting.ipynb 51
def plot_tree_dtreeviz(estimator, # sklearn's classifier
                       X, # Training features
                       y, # Training label
                       target_name:str, # The (string) name of the target variable; e.g., for Titanic, it's "Survived"
                       class_names:list=None, # List of names associated with the labels (same order); e.g. ['no','yes']
                       tree_index=0, # Index (from 0) of tree if model is an ensemble of trees like a random forest.
                       depth_range_to_display=None, # Range of depth levels to be displayed. The range values are inclusive
                       fancy=False, # To draw fancy tree chart (as opposed to simplified one)
                       scale=1.0 # Scale of the chart. Higher means bigger
                      ):
    "Plot a decision tree using dtreeviz. Note that you need to install graphviz before using this function"
    viz = dtreeviz.model(estimator,X,y,tree_index=tree_index,target_name=target_name,
                        feature_names=X.columns.values,
                        class_names=class_names,
                        )
    
    return viz.view(depth_range_to_display=depth_range_to_display,
         orientation='LR',
         instance_orientation='LR',fancy=fancy,scale=scale)

# %% ../nbs/03_chart_plotting.ipynb 57
def plot_classification_tree_sklearn(estimator, # sklearn's classifier
                      feature_names, # List of names of dependent variables (features)
                      class_names:list, # List of names associated with the labels (same order); e.g. ['no','yes']
                      rotate=True, # To rotate the tree graph
                      fname='tmp' # Name of the png file to save(no extension)
                     ):
    "Plot a decision tree classifier using sklearn. Note that this will output a png file with fname instead of showing it in the notebook"
    s = export_graphviz(estimator,out_file=None,feature_names=feature_names,filled=True,class_names=class_names,
                       special_characters=True,rotate=rotate,rounded=True)
    graph = graphviz.Source(s,format='png')
    
    _path = Path('./images')
    create_dir(_path)
    graph.render(_path/fname)

# %% ../nbs/03_chart_plotting.ipynb 65
def plot_feature_importances(importances, # feature importances from sklearn's **feature_importances_** variable
                             feature_names, # List of names of dependent variables (features)
                             figsize=(20,10), # Matplotlib figsize
                             top_n=None # Show top n features
                            ):
    "Plot and return a dataframe of feature importances, using sklearn's **feature_importances_** value"
    fea_imp_df = pd.DataFrame(data={'Feature':feature_names,'Importance':importances}).set_index('Feature')
    fea_imp_df = fea_imp_df.sort_values('Importance', ascending=True)
    if top_n is not None:
        fea_imp_df = fea_imp_df.tail(top_n)
    fea_imp_df.plot(kind='barh',figsize=figsize)
    plt.show()
    return fea_imp_df

# %% ../nbs/03_chart_plotting.ipynb 69
def plot_permutation_importances(model, # sklearn tree model that has been trained
                                 X, # Training features
                                 y, # Training label
                                 scoring=['f1_macro'], # metric, or a list of metrics
                                 n_repeats=5, # Number of times to permute a feature (higher means more accurate)
                                 seed=42, # Random seed
                                 top_n=None, # Show top n features
                                 figsize=(20,10) # Matplotlib figsize
                                ):
    "Plot and return a dataframe of feature importances using sklearn.inspection.permutation_importance"
    scoring = val2list(scoring)
    r_multi = permutation_importance(model, X, y, n_repeats=n_repeats, random_state=seed, scoring=scoring)
    fea_imp_dfs=[]
    for metric in r_multi.keys():
        print(f"{metric}")
        r = r_multi[metric]        
        fea_imp_df  = pd.DataFrame(data={'Feature':X.columns.values,'Importance':r['importances_mean'],'STD':r['importances_std']}).set_index('Feature')
        fea_imp_df = fea_imp_df.sort_values(['Importance'],ascending=True)
        if top_n is not None:
            fea_imp_df = fea_imp_df.tail(top_n)
        fig, ax = plt.subplots()
        fea_imp_df['Importance'].plot(kind='barh',figsize=figsize,xerr=fea_imp_df['STD'],ax=ax)
        ax.set_title("Feature importances using permutation")
        ax.set_ylabel("Mean metric decrease")
        fig.tight_layout()
        plt.show()
        fea_imp_dfs.append(fea_imp_df)
    return fea_imp_dfs

# %% ../nbs/03_chart_plotting.ipynb 73
def params_2D_heatmap(search_cv:dict, # A dict with keys as column headers and values as columns. Typically an attribute (**cv_results_**) of GridSearchCV or RandomizedSearchCV
                      param1:str, # Name of the first hyperparameter
                      param2:str, # Name of the second hyperparameter
                      scoring:str='f1_macro', # Metric name 
                      log_param1=False, # To log the first hyperparameter
                      log_param2=False, # To log the second hyperparameter
                      figsize=(20,10), # Matplotlib figsize
                      min_hm=None, # Minimum value for the metric to show
                      max_hm=None, # Maximum value of the metric to show
                      higher_is_better=True): # Set if high metric is better
    "Plot 2D graph of metric value for each pair of hyperparameters"
    rs_df = pd.DataFrame(search_cv)
    cm = plt.cm.get_cmap('RdYlBu')
    z = rs_df[f'mean_test_{scoring}'].values
    if not higher_is_better:
        z*=-1
    x = rs_df[f'param_{param1}'].values
    y = rs_df[f'param_{param2}'].values
    plt.figure(figsize=figsize)
    sc = plt.scatter(x, y, c=z, vmin=z.min() if not min_hm else min_hm, vmax=z.max() if not max_hm else max_hm, s=20, cmap=cm)
    if log_param2:
        plt.yscale('log')
    if log_param1:
        plt.xscale('log')
    plt.colorbar(sc)
    plt.xlabel(param1)
    plt.ylabel(param2)
    plt.grid()
    plt.show()

# %% ../nbs/03_chart_plotting.ipynb 78
def params_3D_heatmap(search_cv:dict, # A dict with keys as column headers and values as columns. Typically an attribute (**cv_results_**) of GridSearchCV or RandomizedSearchCV
                      param1:str, # Name of the first hyperparameter
                      param2:str, # Name of the second hyperparameter
                      param3:str, # Name of the third hyperparameter
                      scoring:str='f1_macro', # Metric name 
                      log_param1=False, # To log the first hyperparameter
                      log_param2=False, # To log the second hyperparameter
                      log_param3=False # To log the third hyperparameter
                     ):
    "Plot 3D graph of metric value for each triplet of hyperparameters"
    rs_df = pd.DataFrame(search_cv)
    scores = rs_df[f'mean_test_{scoring}'].values
    fig = px.scatter_3d(rs_df, x=f'param_{param1}', y=f'param_{param2}', z=f'param_{param3}',
                    color=f'mean_test_{scoring}',range_color=[scores.min(),scores.max()],
                       log_x = log_param1, log_y=log_param2, log_z=log_param3)
    fig.show()

# %% ../nbs/03_chart_plotting.ipynb 82
def pdp_numerical_only(model, # sklearn tree model that has been trained
                       X:pd.DataFrame, # dataframe to perform pdp
                       num_features:list, # A list of numerical features
                       class_names:list, # List of names associated with the labels (same order); e.g. ['no','yes']
                       y_colors=None, # List of colors associated with class_names
                       ncols=2,
                       nrows=2,
                       figsize=(20,16)):
    "Plot PDP plot for numerical dependent variables"
    common_params = {
    "subsample": 40,
    "n_jobs": -1,
    "grid_resolution": 100,
    "random_state": 42,
    }
    
    num_features = val2list(num_features)
    features_info = {
        # features of interest
        "features": num_features,
        # type of partial dependence plot
        "kind": "average",
        # information regarding categorical features
        "categorical_features": None,
    }
    
    if ncols*nrows!=len(num_features):
        raise ValueError('Make sure the product of ncols and nrows is exactly the number of numerical features you want to plot')
    _, ax = plt.subplots(ncols=ncols, nrows=nrows, squeeze=False,figsize=figsize,constrained_layout=True)
    
    if y_colors is None:
        y_colors = matplotlib.colormaps['tab10'].colors

    for i in range(len(class_names)):
        _display = PartialDependenceDisplay.from_estimator(
                            model,
                            X,
                            **features_info,
                            target=i,
                            line_kw={"label": class_names[i],'color':y_colors[i]},
                            ax=ax,
                            **common_params
        )

# %% ../nbs/03_chart_plotting.ipynb 89
def pdp_categorical_only(model, # sklearn tree model that has been trained
                         X:pd.DataFrame, # dataframe to perform pdp
                         cat_feature:list, # A single categorical feature
                         class_names:list, # List of names associated with the labels (same order); e.g. ['no','yes']
                         y_colors=None, # List of colors associated with class_names
                         ymax=0.5,
                         figsize=(20,8)):
    "Plot PDP plot for categorical dependent variables"
    common_params = {
    "subsample": 40,
    "n_jobs": 2,
    "grid_resolution": 100,
    "random_state": 42,
    }
    
    features_info = {
        # features of interest
        "features": [cat_feature],
        # type of partial dependence plot
        "kind": "average",
        # information regarding categorical features
        "categorical_features": [cat_feature],
    }
    if y_colors is None:
        y_colors = matplotlib.colormaps['tab10'].colors

    displays=[]
    for i in range(len(class_names)): 
        _, ax = plt.subplots(figsize=(1,1))

        _display = PartialDependenceDisplay.from_estimator(
            model,
            X,
            **features_info,
            target=i,
            line_kw={"label": class_names[i],'color':y_colors[i]},
            ax=ax,
            **common_params,
        );
        displays.append(_display)
    
    fig, axes = plt.subplots(1, len(displays), figsize=figsize,sharey=True)
    for i in range(len(displays)):
        displays[i].plot(ax=axes[i],pdp_lim={1: (0, ymax)})
        axes[i].set_title(class_names[i])

# %% ../nbs/03_chart_plotting.ipynb 92
def plot_ice_pair(model, # sklearn tree model that has been trained
                  X:pd.DataFrame, # dataframe to perform ice
                  pair_features:list, # a list of only 2 features
                  class_idx, # index of the class to plot
                  figsize=(10,4)):
    "Plot ICE plot from a pair of numerical feature"
    common_params = {
        "subsample": 40,
        "n_jobs": -1,
        "grid_resolution": 100,
        "random_state": 42,
    }
    fea_to_plot = pair_features
    features_info = {
        # features of interest
        "features": [fea_to_plot[0],fea_to_plot[1], fea_to_plot],
        # type of partial dependence plot
        "kind": "average",
        # information regarding categorical features
        "categorical_features": None,
    }

    _, ax = plt.subplots(ncols=3, figsize=figsize, constrained_layout=True)

    _display = PartialDependenceDisplay.from_estimator(
        model,
        X,
        **features_info,
        target=class_idx,
        ax=ax,
        **common_params,
    )
    plt.setp(_display.deciles_vlines_, visible=False)

# %% ../nbs/03_chart_plotting.ipynb 98
def plot_confusion_matrix(y_true:list|np.ndarray, # A list/numpy array of true labels 
                          y_pred:list|np.ndarray, # A list/numpy array of predictions
                          labels=None # Display names matching the labels (same order).
                         ):
    "Simple function to plot the confusion matrix"
    cm = confusion_matrix(y_true, y_pred)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm,
                                  display_labels=labels)
    disp.plot()
    plt.show()

# %% ../nbs/03_chart_plotting.ipynb 102
def draw_sankey(data, target,chart_name,save_name=None):
    PATH = Path('sk_reports')
    unique_source_target = list(pd.unique(data[['source', 'target']].values.ravel('K')))
    mapping_dict = {k: v for v, k in enumerate(unique_source_target)}
    data = data.copy()
    data['source'] = data['source'].map(mapping_dict)
    data['target'] = data['target'].map(mapping_dict)
    links_dict = data.to_dict(orient='list')

    nodes = np.unique(data[["source", "target"]], axis=None)
    nodes = pd.Series(index=nodes, data=range(len(nodes)))


    fig = go.Figure(data=[go.Sankey(
        node = dict(
          pad = 15,
          thickness = 20,
          line = dict(color = "black", width = 0.5),
          label = unique_source_target,
          # color = [px.colors.qualitative.Plotly[i % len(px.colors.qualitative.Plotly)] for i in nodes.loc[data["source"]]]
        ),
        link = dict(
          source = links_dict["source"],
          target = links_dict["target"],
          value = links_dict[target],
          color = [px.colors.qualitative.Plotly[i % len(px.colors.qualitative.Plotly)] for i in nodes.loc[data["source"]]],
      ))])
    fig.update_layout(title_text=chart_name, font_size=10)
    fig.show()
    if save_name: fig.write_html(str(PATH/save_name)+ '.html')
