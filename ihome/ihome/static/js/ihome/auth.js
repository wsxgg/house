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
    // 显示已实名认证信息
    $.get("/api/v1.0/users/auth", function(resp){
        real_name = resp.data.real_name;
        id_card = resp.data.id_card;
        $("#real-name").val(real_name);
        $("#id-card").val(id_card);
    })

    // 添加实名认证
    $("#form-auth").submit(function(e){
        // 阻止表单的默认行为
        e.preventDefault();
        // 1. 获取表单数据
        real_name = $('#real-name').val();
        id_card = $('#id-card').val();
        var req_data = {
            "real_name": real_name,
            "id_card": id_card 
        }   
        var req_json = JSON.stringify(req_data);
        $.ajax({
            url: "/api/v1.0/users/auth",
            type: "post",
            data: req_json,
            contentType: "application/json",
            dataType: "json",
            headers: {"X-CSRFToken": getCookie("csrf_token")},
            success: function(resp){
                if (resp.errno == "0"){
                    showSuccessMsg();
                }
                else {
                    $(".error-msg").show();
                }
            }
        })
    })

    // 当聚焦输入框，取消用户名重复提示
    $("#id-card").focus(function(){
        $(".error-msg").hide();
    })
})
