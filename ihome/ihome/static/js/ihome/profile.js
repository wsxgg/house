/*
 * @Author: your name
 * @Date: 2020-05-21 17:08:15
 * @LastEditTime: 2020-05-26 08:35:28
 * @LastEditors: Please set LastEditors
 * @Description: In User Settings Edit
 * @FilePath: \ihome\ihome\static\js\ihome\profile.js
 */ 
function showSuccessMsg() {
    $('.popup_con').fadeIn('fast', function() {
        setTimeout(function(){
            $('.popup_con').fadeOut('fast',function(){}); 
        },1000) 
    });
}

function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(document).ready(function(){
    // 页面刷新
    $.get("/api/v1.0/users", function(resp){
        if (resp.errno == "0"){
            avatar_url = resp.data.avatar_url;
            name = resp.data.name;
            $("#user-avatar").attr("src", avatar_url);
            $("#user-name").val(name);
        }
    })

    // 提交头像
    $("#form-avatar").submit(function(e){
        // 组织表单的默认行为
        e.preventDefault();
        // 自定义发送表单数据
        // 利用jquery.form.min.js提供的ajaxSubmit对表单进行异步提交
        $(this).ajaxSubmit({
            url: "/api/v1.0/users/avatar",
            type: "post",
            headers: {"X-CSRFToken": getCookie("csrf_token")},
            dataType: "json",
            success: function(resp){
                if (resp.errno == "0"){
                    // 上传成功
                    var avatar_url = resp.data.avatar_url;
                    $("#user-avatar").attr("src", avatar_url);
                }
                else {
                    alert(resp.errmsg);
                }
            }
        })
    });

    // 提交用户名
    $("#form-name").submit(function(e){
        // 组织默认提交事件发生
        e.preventDefault();
        // 自定义提交事件
        // 获取表单参数
        var user_name = $("#user-name").val();
        var req_data = {
            "user_name": user_name,
        }
        var req_json = JSON.stringify(req_data);
        // 发送ajax请求
        $.ajax({
            url: "/api/v1.0/users/name",
            type: "post",
            data: req_json,
            contentType: "application/json",
            dataType: "json",
            headers: {"X-CSRFToken": getCookie("csrf_token")},
            success: function(resp){
                // 修改成功
                if (resp.errno == "0" ){
                    showSuccessMsg();
                }
                // 用户名重复
                else if (resp.errmsg == "用户名已存在" ){
                    $(".error-msg").show();
                }
                else {
                    alert(resp.errmsg);                    
                }               
            }
        });
    })

    // 当聚焦输入框，取消用户名重复提示
    $("#user-name").focus(function(){
        $(".error-msg").hide()
    })

});

