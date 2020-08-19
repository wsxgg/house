/*
 * @Author: your name
 * @Date: 2020-05-21 17:08:15
 * @LastEditTime: 2020-05-24 17:08:00
 * @LastEditors: Please set LastEditors
 * @Description: In User Settings Edit
 * @FilePath: \ihome\ihome\static\js\ihome\my.js
 */ 

function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}
// 退出登录事件
function logout() {
    $.ajax({
        url: "api/v1.0/sessions",
        type: "delete",
        headers: {"X-CSRFToken": getCookie("csrf_token")},
        dataType: "json",
        success: function(data){
            if (data.errno == "0"){
                location.href = "/"
            }
        }
    })
}

$(document).ready(function(){
    // 获取页面，显示用户名和手机号,头像
    $.get("/api/v1.0/myinfo", function(resp){
        var name = resp.data.name;
        var mobile = resp.data.mobile;
        var avatar = resp.data.avatar;
        $(".menu-content .menu-text h3 span").html(name);
        $(".menu-content .menu-text h5 span").html(mobile);
        $("#user-avatar").attr('src', avatar);
    })
})