function hrefBack() {
    history.go(-1);
}

function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

// 获取url参数
function decodeQuery(){
    var search = decodeURI(document.location.search);
    return search.replace(/(^\?)/, '').split('&').reduce(function(result, item){
        values = item.split('=');
        result[values[0]] = values[1];
        return result;
    }, {});
}

function showErrorMsg() {
    $('.popup_con').fadeIn('fast', function() {
        setTimeout(function(){
            $('.popup_con').fadeOut('fast',function(){}); 
        },1000) 
    });
}

$(document).ready(function(){
    $(".input-daterange").datepicker({
        format: "yyyy-mm-dd",
        startDate: "today",
        language: "zh-CN",
        autoclose: true
    });
    $(".input-daterange").on("changeDate", function(){
        var startDate = $("#start-date").val();
        var endDate = $("#end-date").val();

        if (startDate && endDate && startDate > endDate) {
            showErrorMsg();
        } else {
            var sd = new Date(startDate);
            var ed = new Date(endDate);
            days = (ed - sd)/(1000*3600*24) + 1;
            var price = $(".house-text>p>span").html();
            var amount = days * parseFloat(price);
            $(".order-amount>span").html(amount.toFixed(2) + "(共"+ days +"晚)");
        }
    });

    // 获取url参数
    var queryData = decodeQuery();
    var houseId = queryData['hid'];

    // 获取房屋基本信息
    $.get("/api/v1.0/houses/" + houseId, function(resp){
        if (resp.errno == "0"){
            $(".house-info>img").attr("src", resp.data.house.img_urls[0]);
            $(".house-text>h3").html(resp.data.house.title);
            $(".house-text>p>span").html((resp.data.house.price/100.0).toFixed(0));
        }
    });

    // 提交订单
    $(".submit-btn").on("click", function(e){
        if ($(".order-amount>span").html()){
            $(this).prop("disabled", true);
            // 获取参数
            var startDate = $("#start-date").val();
            var endDate = $("#end-date").val();
            // 组织参数
            var data = {
                "house_id":houseId,
                "start_date":startDate,
                "end_date":endDate
            }
            // 发送ajax请求
            $.ajax({
                url:"/api/v1.0/orders",
                type:"POST",
                data:JSON.stringify(data),
                contentType:"application/json",
                dataType:"json",
                headers:{"X-CSRFToken": getCookie("csrf_token")},
                success:function(resp){
                    // 如果未登陆
                    if (resp.errno == "4101"){
                        location.href = "/login.html";
                    }
                    // 下单失败
                    else if (resp.errno == "4004"){
                        showErrorMsg("房间已被抢定，请重新选择日期！");
                    } 
                    // 下单成功，跳转到我的订单页面
                    else if (resp.errno == "0"){
                        location.href = "/orders.html";
                    }
                }
            })
        }
    })

})
