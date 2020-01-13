import Dumbledraw.dumbledraw as dd
import Dumbledraw.rootfile_parser_inputshapes as rootfile_parser
import Dumbledraw.styles as styles
import ROOT

import argparse
import copy
import yaml
import os

import logging
logger = logging.getLogger("")
from multiprocessing import Pool
from multiprocessing import Process

def parse_arguments():
    parser = argparse.ArgumentParser(
        description=
        "Plot categories using Dumbledraw from shapes produced by shape-producer module."
    )
    parser.add_argument(
        "-l", "--linear", action="store_true", help="Enable linear x-axis")
    parser.add_argument("-e", "--era", type=str, default="2017", help="Era")
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        required=True,
        help="ROOT file with shapes of processes")
    parser.add_argument(
        "--variables",
        type=str,
        default=None,
        help="Enable control plotting for given variable")
    parser.add_argument(
        "--category-postfix",
        type=str,
        default=None,
        help="Enable control plotting for given category_postfix. Structure of a category: <variable>_<postfix>")
    parser.add_argument(
        "--channels",
        type=str,
        default=None,
        help="Enable control plotting for given variable")
    parser.add_argument(
        "--normalize-by-bin-width",
        action="store_false",
        help="Normelize plots by bin width")
    parser.add_argument(
        "--fake-factor",
        action="store_true",
        help="Fake factor estimation method used")
    parser.add_argument(
        "--embedding",
        action="store_true",
        help="Fake factor estimation method used")

    return parser.parse_args()


def setup_logging(output_file, level=logging.DEBUG):
    logger.setLevel(level)
    formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    file_handler = logging.FileHandler(output_file, "w")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


def main(info):
    args = info["args"]
    variable = info["variable"]
    channel = info["channel"]
    channel_dict = {
        "ee": "ee",
        "em": "e#mu",
        "et": "e#tau_{h}",
        "mm": "#mu#mu",
        "mt": "#mu#tau_{h}",
        "tt": "#tau_{h}#tau_{h}"
    }
    if args.linear == True:
        split_value = 0
    else:
        if args.normalize_by_bin_width:
            split_value = 10001
        else:
            split_value = 101

    split_dict = {c: split_value for c in ["et", "mt", "tt", "em", "mm"]}

    bkg_processes = [
        "QCD", "VVT", "VVL", "VVJ", "W", "TTT", "TTL", "TTJ", "ZJ", "ZL", "ZTT"
    ]
    all_bkg_processes = [b for b in bkg_processes]
    legend_bkg_processes = copy.deepcopy(bkg_processes)
    legend_bkg_processes.reverse()

    if "2016" in args.era:
        era = "Run2016"
    elif "2017" in args.era:
        era = "Run2017"
    elif "2018" in args.era:
        era = "Run2018"
    else:
        logger.critical("Era {} is not implemented.".format(args.era))
        raise Exception

    category = "_".join([channel, variable])
    if args.category_postfix is not None:
        category += "_%s"%args.category_postfix
    rootfile = rootfile_parser.Rootfile_parser(args.input, "smhtt", era, variable, "125")
    bkg_processes = [b for b in all_bkg_processes]
    legend_bkg_processes = copy.deepcopy(bkg_processes)
    legend_bkg_processes.reverse()

    # create plot
    width = 600
    if args.linear == True:
        plot = dd.Plot(
            [0.3, [0.3, 0.28]], "ModTDR", r=0.04, l=0.14, width=width)
    else:
        raise Exception
        plot = dd.Plot(
            [0.5, [0.3, 0.28]], "ModTDR", r=0.04, l=0.14, width=width)

    # get background histograms
    total_bkg = None
    for index,process in enumerate(bkg_processes):
        if index == 0:
            total_bkg = rootfile.get(channel, category, process).Clone()
        else:
            total_bkg.Add(rootfile.get(channel, category, process))
        plot.add_hist(
            rootfile.get(channel, category, process), process, "bkg")
        plot.setGraphStyle(
            process, "hist", fillcolor=styles.color_dict[process])

    plot.add_hist(total_bkg, "total_bkg")
    plot.setGraphStyle(
        "total_bkg",
        "e2",
        markersize=0,
        fillcolor=styles.color_dict["unc"],
        linecolor=0)

    plot.add_hist(rootfile.get(channel, category, "data_obs"), "data_obs")
    data_norm = plot.subplot(0).get_hist("data_obs").Integral()
    plot.subplot(0).get_hist("data_obs").GetXaxis().SetMaxDigits(4)
    plot.subplot(0).setGraphStyle("data_obs", "e0")

    # get signal histograms
    plot_idx_to_add_signal = [0,2] if args.linear else [1,2]
    for i in plot_idx_to_add_signal:
        ggH = rootfile.get(channel, category, "ggH125").Clone()
        qqH = rootfile.get(channel, category, "qqH125").Clone()
        if ggH.Integral() > 0:
            ggH_scale = 0.5*data_norm/ggH.Integral()
        else:
            ggH_scale = 0.0
        if qqH.Integral() > 0:
            qqH_scale = 0.5*data_norm/qqH.Integral()
        else:
            qqH_scale = 0.0
        if i in [0,1]:
            ggH.Scale(ggH_scale)
            qqH.Scale(qqH_scale)
        plot.subplot(i).add_hist(ggH, "ggH")
        plot.subplot(i).add_hist(ggH, "ggH_top")
        plot.subplot(i).add_hist(qqH, "qqH")
        plot.subplot(i).add_hist(qqH, "qqH_top")

    plot.subplot(0 if args.linear else 1).setGraphStyle(
        "ggH", "hist", linecolor=styles.color_dict["ggH"], linewidth=3)
    plot.subplot(0 if args.linear else 1).setGraphStyle("ggH_top", "hist", linecolor=0)
    plot.subplot(0 if args.linear else 1).setGraphStyle(
        "qqH", "hist", linecolor=styles.color_dict["qqH"], linewidth=3)

    # assemble ratio
    bkg_ggH = plot.subplot(2).get_hist("ggH")
    bkg_qqH = plot.subplot(2).get_hist("qqH")
    bkg_ggH.Add(plot.subplot(2).get_hist("total_bkg"))
    bkg_qqH.Add(plot.subplot(2).get_hist("total_bkg"))
    plot.subplot(2).add_hist(bkg_ggH, "bkg_ggH")
    plot.subplot(2).add_hist(bkg_ggH, "bkg_ggH_top")
    plot.subplot(2).add_hist(bkg_qqH, "bkg_qqH")
    plot.subplot(2).add_hist(bkg_qqH, "bkg_qqH_top")
    plot.subplot(2).setGraphStyle(
        "bkg_ggH",
        "hist",
        linecolor=styles.color_dict["ggH"],
        linewidth=3)
    plot.subplot(2).setGraphStyle("bkg_ggH_top", "hist", linecolor=0)
    plot.subplot(2).setGraphStyle(
        "bkg_qqH",
        "hist",
        linecolor=styles.color_dict["qqH"],
        linewidth=3)
    plot.subplot(2).setGraphStyle("bkg_qqH_top", "hist", linecolor=0)

    plot.subplot(2).normalize([
        "total_bkg", "bkg_ggH", "bkg_ggH_top", "bkg_qqH",
        "bkg_qqH_top", "data_obs"
    ], "total_bkg")

    # stack background processes
    plot.create_stack(bkg_processes, "stack")

    # normalize stacks by bin-width
    if args.normalize_by_bin_width:
        plot.subplot(0).normalizeByBinWidth()
        plot.subplot(1).normalizeByBinWidth()

    # set axes limits and labels
    plot.subplot(0).setYlims(
        split_dict[channel],
        max(2 * plot.subplot(0).get_hist("data_obs").GetMaximum(),
            split_dict[channel] * 2))

    plot.subplot(2).setYlims(0.45, 2.05)
    if category in ["2"]:
        plot.subplot(2).setYlims(0.45, 2.05)
    if category in ["1", "2"]:
        plot.subplot(0).setYlims(0.1, 150000000)
        if channel == "em":
            plot.subplot(0).setYlims(1, 15000000)

    if args.linear != True:
        plot.subplot(1).setYlims(0.1, split_dict[channel])
        plot.subplot(1).setYlabel(
            "")  # otherwise number labels are not drawn on axis
    if variable != None:
        if variable in styles.x_label_dict[channel]:
            x_label = styles.x_label_dict[channel][
                variable]
        else:
            x_label = variable
        plot.subplot(2).setXlabel(x_label)
    else:
        plot.subplot(2).setXlabel("NN output")
    if args.normalize_by_bin_width:
        plot.subplot(0).setYlabel("dN/d(NN output)")
    else:
        plot.subplot(0).setYlabel("N_{events}")

    plot.subplot(2).setYlabel("")

    plot.scaleYLabelSize(0.8)
    plot.scaleYTitleOffset(1.1)

    if not channel == "tt" and category in ["11", "12", "13", "14", "15", "16"]:
        plot.subplot(2).changeXLabels(["0.2", "0.4", "0.6", "0.8", "1.0"])

    # draw subplots. Argument contains names of objects to be drawn in corresponding order.
    procs_to_draw = ["stack", "total_bkg", "data_obs"] if args.linear else ["stack", "total_bkg", "data_obs"]
    plot.subplot(0).Draw(procs_to_draw)
    if args.linear != True:
        plot.subplot(1).Draw([
            "stack", "total_bkg","data_obs"
        ])
    plot.subplot(2).Draw([
        "total_bkg", "data_obs"
    ])


    # create legends
    suffix = ["", "_top"]
    for i in range(2):

        plot.add_legend(width=0.6, height=0.15)
        for process in legend_bkg_processes:
            plot.legend(i).add_entry(
                0, process, styles.legend_label_dict[process.replace("TTL", "TT").replace("VVL", "VV").replace("NLO","")], 'f')
        plot.legend(i).add_entry(0, "total_bkg", "Bkg. stat. unc.", 'f')
        if "mm" not in channel:
            plot.legend(i).add_entry(0 if args.linear else 1, "ggH%s" % suffix[i], "%s #times gg#rightarrowH"%str(int(ggH_scale)), 'l')
            plot.legend(i).add_entry(0 if args.linear else 1, "qqH%s" % suffix[i], "%s #times qq#rightarrowH"%str(int(qqH_scale)), 'l')
        plot.legend(i).add_entry(0, "data_obs", "Data", 'PE')
        plot.legend(i).setNColumns(3)
    plot.legend(0).Draw()
    plot.legend(1).setAlpha(0.0)
    plot.legend(1).Draw()

    for i in range(2):
        plot.add_legend(
            reference_subplot=2, pos=1, width=0.5, height=0.03)
        plot.legend(i + 2).add_entry(0, "data_obs", "Data", 'PE')
        if "mm" not in channel:
            plot.legend(i + 2).add_entry(0 if args.linear else 1, "ggH%s" % suffix[i],
                                         "ggH+bkg.", 'l')
            plot.legend(i + 2).add_entry(0 if args.linear else 1, "qqH%s" % suffix[i],
                                         "qqH+bkg.", 'l')
        plot.legend(i + 2).add_entry(0, "total_bkg", "Bkg. stat. unc.", 'f')
        plot.legend(i + 2).setNColumns(4)
    plot.legend(2).Draw()
    plot.legend(3).setAlpha(0.0)
    plot.legend(3).Draw()

    # draw additional labels
    plot.DrawCMS()
    if "2016" in args.era:
        plot.DrawLumi("35.9 fb^{-1} (2016, 13 TeV)")
    elif "2017" in args.era:
        plot.DrawLumi("41.5 fb^{-1} (2017, 13 TeV)")
    elif "2018" in args.era:
        plot.DrawLumi("59.7 fb^{-1} (2018, 13 TeV)")
    else:
        logger.critical("Era {} is not implemented.".format(args.era))
        raise Exception

    posChannelCategoryLabelLeft = None
    plot.DrawChannelCategoryLabel(
        "%s, %s" % (channel_dict[channel], "inclusive"),
        begin_left=posChannelCategoryLabelLeft)

    # save plot
    if not args.embedding and not args.fake_factor:
        postfix = "fully_classic"
    if args.embedding and not args.fake_factor:
        postfix = "emb_classic"
    if not args.embedding and args.fake_factor:
        postfix = "classic_ff"
    if args.embedding and args.fake_factor:
        postfix = "emb_ff"

    plot.save("%s.%s" % (variable, "pdf"))
    plot.save("%s.%s" % (variable, "png"))


if __name__ == "__main__":
    setup_logging("plot.log", logging.INFO)
    args = parse_arguments()
    args.linear = True
    variables = args.variables.split(",")
    channels = args.channels.split(",")
    infolist = []
    for ch in channels:
        for v in variables:
            infolist.append({"args" : args, "channel" : ch, "variable" : v})
    for info in infolist:
        main(info)
