/*
 * @Author: your name
 * @Date: 2020-05-21 17:08:15
 * @LastEditTime: 2020-05-24 16:51:24
 * @LastEditors: Please set LastEditors
 * @Description: In User Settings Edit
 * @FilePath: \ihome\ihome\static\js\ihome\login.js
 */ 
function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(document).ready(function() {
    $("#mobile").focus(function(){
        $("#mobile-err").hide();
    });
    $("#password").focus(function(){
        $("#password-err").hide();
    });
    $(".form-login").submit(function(e){
        // 取消表单默认提交行为
        e.preventDefault();
        mobile = $("#mobile").val();
        passwd = $("#password").val();
        if (!mobile) {
            $("#mobile-err span").html("请填写正确的手机号！");
            $("#mobile-err").show();
            return;
        } 
        if (!passwd) {
            $("#password-err span").html("请填写密码!");
            $("#password-err").show();
            return;
        }
        // 保存表单数据
        var req_data = {
            mobile: mobile,
            password: passwd
        };
        // 将req_data数据转成jason数据
        var req_json = JSON.stringify(req_data);
        $.ajax({
            url: "/api/v1.0/sessions",
            type: "post",
            data: req_json,
            contentType: "application/json",
            dataType: 'json',
            headers: {
                "X-CSRFToken": getCookie("csrf_token")      
            },     // 将csrf_token值放在请求中， 方便后端csrf验证
            success: function(data){
                if (data.errno == "0"){
                    // 成功时，返回主页
                    location.href = "/";
                }
                else {
                    // 显示错误信息
                    $("#password-err span").html(data.errmsg);
                    $("#password-err").show();
                }
            }
        })
    });
})