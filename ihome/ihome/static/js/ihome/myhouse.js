$(document).ready(function(){
    $.get("/api/v1.0/users/auth", function(resp){
        if (resp.errno == "4101"){
            // 用户未登录
            location.href = "/login.html";
        }
        else if (resp.errno == "0"){
            if (!(resp.data.real_name && resp.data.id_card)){
                // 用户未实名认证
                $(".auth-warn").show();
                $(".new-house").hide();
            }
            // 已认证的用户，请求其之前访发布的房源
            $.get("/api/v1.0/user/houses", function(resp){
                if (resp.errno == "0"){
                    var html = template("houses-list-tmpl", {houses: resp.data.houses});
                    $("#houses-list").html(html);
                }
                else {
                    var html = template("houses-list-tmpl", {houses:[]});
                    $("#houses-list").html(html);
                }
            })
        }
    });
})