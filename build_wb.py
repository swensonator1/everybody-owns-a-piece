"""Builds the round-two workbook."""
import sys, json, os
from build_wb_part1 import *
import wb_data, wb_switch, wb_model, wb_tabs, wb_final

ORDER = ['Start here', 'Switches', 'Best combination', 'Stress tests', 'Model', 'Workers', 'Scenarios', 'Joe 40 years',
         'Who paid', 'Government', 'Day one', 'Ad levy', 'Number labels', 'Engine check', 'Data', 'Sources']


def build(path, tested=None):
    B = Book()
    for n in ORDER:
        B.sheet(n)
    wb_data.build_data(B); wb_data.build_sources(B)
    wb_switch.build_switches(B); wb_switch.build_scenarios(B)
    wb_tabs.build_adlevy(B)
    wb_model.build_model(B); wb_model.build_workers(B)
    wb_tabs.build_joe(B); wb_tabs.build_whopaid(B); wb_tabs.build_government(B); wb_tabs.build_dayone(B)
    wb_final.build_stress(B); wb_final.build_best(B); wb_final.build_labels(B); wb_final.build_check(B, tested); wb_final.build_start(B)
    B.wb.active = 0
    B.wb.save(path)
    json.dump(dict(addr=B.addr, MR=wb_model.MR, SW=wb_switch.SW, WR=wb_model.WR), open(path + '.addr.json', 'w'), indent=0)
    return B


if __name__ == '__main__':
    tested = json.load(open(sys.argv[2])) if len(sys.argv) > 2 and os.path.exists(sys.argv[2]) else None
    build(sys.argv[1] if len(sys.argv) > 1 else 'wb_test.xlsx', tested)
    print('saved')
