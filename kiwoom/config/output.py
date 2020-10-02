from kiwoom.wrapper.api import API


api = API


VOID = [
    api.set_input_value, api.disconnect_real_data,
]


LONG = [
    api.comm_connect, api.comm_rq_data, api.send_order,
    api.get_repeat_cnt, api.comm_kw_rq_data, api.get_connect_state,
    api.get_master_listed_stock_cnt,

]


BSTR = [
    api.get_login_info, api.get_code_list_by_market, api.get_master_code_name,
    api.get_master_construction, api.get_master_listed_stock_date, api.get_master_last_price,

]


# api.set_output_fid
# api.get_api_module_path
# get_data_count
# get_output_value
# GetThemeGroupList
# GetThemeGroupCode
# GetFutureCodeByIndex
# GetOptionCodeByMonth
# GetOptionCodeByActPrice
# GetSFutureList
# GetSFutureCodeByIndex
# GetSActPriceList
# GetSMonthList
# GetSOptionCode
# GetSOptionCodeByMonth
# GetSOptionCodeByActPrice
# GetSFOBasisAssetList
# GetSOptionATM


