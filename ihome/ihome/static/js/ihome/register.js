// js中读取cookie的方法
function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

//  保存图片验证码编号
var imageCodeId = "";

// 生成随机数，用于生成image_code_id
function generateUUID() {
    var d = new Date().getTime();
    if(window.performance && typeof window.performance.now === "function"){
        d += performance.now(); //use high-precision timer if available
    }
    var uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = (d + Math.random()*16)%16 | 0;
        d = Math.floor(d/16);
        return (c=='x' ? r : (r&0x3|0x8)).toString(16);
    });
    return uuid;
}

// 获取验证码图片
function generateImageCode() {
    // 形成图片验证码的后端地址，设置到页面中，让浏览器请求图片
    // 1. 生成图片验证码的编号, imageCodeId有定义全局变量
    imageCodeId = generateUUID();
    // 2. 指示图片url
    var url="/api/v1.0/image_code/" + imageCodeId
    $(".image-code img").attr("src", url)
}

// 点击发送验证码的时候执行
function sendSMSCode() {
    $(".phonecode-a").removeAttr("onclick");
    var mobile = $("#mobile").val();
    if (!mobile) {
        $("#mobile-err span").html("请填写正确的手机号！");
        $("#mobile-err").show();
        $(".phonecode-a").attr("onclick", "sendSMSCode();");
        return;
    } 
    var imageCode = $("#imagecode").val();
    if (!imageCode) {
        $("#image-code-err span").html("请填写验证码！");
        $("#image-code-err").show();
        $(".phonecode-a").attr("onclick", "sendSMSCode();");
        return;
    }
    // 构建请求数据
    var reg_data = {
        image_code: imageCode,   // 图片验证码
        image_code_id: "image_code_"+imageCodeId    // 图片验证码编号 （全局变量有定义）
    }
    // 向后端发送请求
    $.get("/api/v1.0/sms_code/"+mobile, reg_data, function(resp){
        if (resp.errno == "0"){
            // 发送成功
            var num = 60;
            // 创建定时器60s，定时“获取验证码”按钮
            var timer = setInterval(function(){
                // 修改倒计时文本
                if (num>1){
                    $(".phonecode-a").html(num+'秒');
                    num -= 1;
                }
                else{
                    $(".phonecode-a").html("获取验证码");
                    $(".phonecode-a").attr("onclick", "sendSMSCode();");
                    clearInterval(timer);
                }
            }, 1000, 60);
        }
        else {
            alert(resp.errmsg);
            $(".phonecode-a").attr("onclick", "sendSMSCode();");
        }
    });
}

$(document).ready(function() {
    generateImageCode();        
    $("#mobile").focus(function(){
        $("#mobile-err").hide();
    });
    $("#imagecode").focus(function(){
        $("#image-code-err").hide();
    });
    $("#phonecode").focus(function(){
        $("#phone-code-err").hide();
    });
    $("#password").focus(function(){
        $("#password-err").hide();
        $("#password2-err").hide();
    });
    $("#password2").focus(function(){
        $("#password2-err").hide();
    });

    // 为表单的提交补充自定义的函数行为，参数e为默认事件--此时为提交表单
    $(".form-register").submit(function(e){
        e.preventDefault();         // 阻止该事件发生
        var mobile = $("#mobile").val();
        var phoneCode = $("#phonecode").val();
        var passwd = $("#password").val();
        var passwd2 = $("#password2").val();
        if (!mobile) {
            $("#mobile-err span").html("请填写正确的手机号！");
            $("#mobile-err").show();
            return;
        } 
        if (!phoneCode) {
            $("#phone-code-err span").html("请填写短信验证码！");
            $("#phone-code-err").show();
            return;
        }
        if (!passwd) {
            $("#password-err span").html("请填写密码!");
            $("#password-err").show();
            return;
        }
        if (passwd != passwd2) {
            $("#password2-err span").html("两次密码不一致!");
            $("#password2-err").show();
            return;
        }
        // ajax向后端发送请求
        // 先构造json的数据
        var req_data = {
            "mobile": mobile,
            "sms_code": phoneCode,
            "password": passwd,
            "password2": passwd2
        }
        var req_json = JSON.stringify(req_data)     //转成json数据
        // 发送
        $.ajax({
            url: '/api/v1.0/users',
            type: "post",
            data: req_json,
            contentType: "application/json",
            dataType: "json",  // 后端回传的格式
            headers: {
                "X-CSRFToken": getCookie("csrf_token")      
            },     // 将csrf_token值放在请求中， 方便后端csrf验证
            success: function(resp){
                if (resp.errno == "0"){
                    // 注册成功，跳转到主页
                    location.href = "/index.html" 
                }
                else {
                    alert(resp.errmsg);
                }
            }
        })
    });
})