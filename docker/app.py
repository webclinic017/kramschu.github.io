#*********************************************************************************************
# Author: Tommy Armstrong
# Date: 1/31/2021
# Class: CS 467 - Capstone
# Group: Resilient Algorithmic Trading Strategies
# Members: Tommy Armstrong, Kimberly Kramschuster, Kepe Bonner, Jillian Crawley
# 
# File: app.py
# Purpose:  Backend API running in the docker container hosting the Quant Connect Lean Engine
#           that receives requests from the user interface and returns results from backtests
# Run Command: python app.py
#
# Module References:
#  Sed:
#    http://unixmysimpleview.blogspot.com/2010/03/sed-more-intro.html
#    https://superuser.com/questions/112834/how-to-match-whitespace-in-sed
#    https://stackoverflow.com/questions/8822097/how-to-replace-a-whole-line-with-sed
#    https://www.gnu.org/software/sed/manual/html_node/Command_002dLine-Options.html
#    https://www.cyberciti.biz/faq/unix-linux-sed-match-replace-the-entire-line-command/
# 
#  JSON:
#    https://www.programiz.com/python-programming/json
#
#  Flask:
#    https://flask.palletsprojects.com/en/1.1.x/
#    https://stackoverflow.com/questions/15562446/how-to-stop-flask-application-without-using-ctrl-c
#    
#**********************************************************************************************

from flask import Flask, make_response, render_template, request, jsonify
import json
import os

app = Flask(__name__)

@app.route('/')
def root():                  
    return 'Hello World'


@app.route('/algorithm', methods=['POST'])
def run_algorithm():
    params = request.get_json()
    print('***********')
    print('***********')
    print(params)

    # Begin modifying files to match specification of requested algorithm backtest
    print('Running sed commands')
    algo = params.get('algorithm')
    # Set the Algorithm Type Name value in the config.json file
    algo_type_command = f'sed -i \'s|^[ \t]*"algorithm-type-name".*|  "algorithm-type-name": "{algo}",|\' /Lean/Launcher/bin/Debug/config.json'
    os.system(algo_type_command)
    # Set the Algorithm Location value in the config.json file
    algo_loc_command = f'sed -i \'s|^[ \t]*"algorithm-location".*|  "algorithm-location": "/Lean/Algorithm.Python/{algo}.py",|\' /Lean/Launcher/bin/Debug/config.json'
    os.system(algo_loc_command)
    print('Finished sed commands')

    # Set the value for the starting cash value in the Algorithm Python file
    print('Setting cash values in Python files')
    cash = params.get('cash')
    cash_command = f'sed -i \'s|^VAR_CASH.*|VAR_CASH={cash}|\' /Lean/Algorithm.Python/{algo}.py'
    os.system(cash_command)
    print('Finished setting cash values in python files')

    # Set the values for the starting date
    print('Setting start date in the python file')
    startlist = params.get('startdate')
    startyear = startlist[0]
    startmonth = startlist[1]
    startday = startlist[2]
    start_year = f'sed -i \'s|^START_YEAR.*|START_YEAR={startyear}|\' /Lean/Algorithm.Python/{algo}.py'
    os.system(start_year)
    start_month = f'sed -i \'s|^START_MONTH.*|START_MONTH={startmonth}|\' /Lean/Algorithm.Python/{algo}.py'
    os.system(start_month)
    start_day = f'sed -i \'s|^START_DAY.*|START_DAY={startday}|\' /Lean/Algorithm.Python/{algo}.py'
    os.system(start_day)
    print('Finished setting up start date in python files')

    # Set the values for the end date
    print('Setting end date in the python file')
    endlist = params.get('enddate')
    endyear = endlist[0]
    endmonth = endlist[1]
    endday = endlist[2]
    end_year = f'sed -i \'s|^END_YEAR.*|END_YEAR={endyear}|\' /Lean/Algorithm.Python/{algo}.py'
    os.system(end_year)
    end_month = f'sed -i \'s|^END_MONTH.*|END_MONTH={endmonth}|\' /Lean/Algorithm.Python/{algo}.py'
    os.system(end_month)
    end_day = f'sed -i \'s|^END_DAY.*|END_DAY={endday}|\' /Lean/Algorithm.Python/{algo}.py'
    os.system(end_day)
    print('Finished setting up ending dates in python files')

    # Set the value for the buy tolerance
    print('Setting buy tolerance in Python files')
    buy_tol = params.get('buytol')
    buy_tol_command = f'sed -i \'s|^BUY_TOL.*|BUY_TOL={buy_tol}|\' /Lean/Algorithm.Python/{algo}.py'
    os.system(buy_tol_command)
    print('Finished setting buy tolerance in python files')

    # Set the value for the sell tolerance
    print('Setting sell tolerance in Python files')
    sell_tol = params.get('selltol')
    sell_tol_command = f'sed -i \'s|^SELL_TOL.*|SELL_TOL={sell_tol}|\' /Lean/Algorithm.Python/{algo}.py'
    os.system(sell_tol_command)
    print('Finished setting sell tolerance in python files')

    # Initiate the backtest run
    print('Launching lean backtest')
    lean_command = 'echo -e "\n" | mono QuantConnect.Lean.Launcher.exe >/dev/null 2>&1'
    os.system(lean_command)
    print('Finished lean backtest')

    # Retrieve the JSON results of the backtest and load them as a dictionary
    print('Loading JSON backtest results file')
    results_fp = f'/Lean/Results/{algo}.json'
    with open(results_fp) as f:
        results = json.load(f)

    # Return the backtest results to the client
    return json.dumps(results)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6004, debug=True)
