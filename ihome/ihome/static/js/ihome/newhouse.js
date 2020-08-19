function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(document).ready(function(){
    // 向后端获取城区信息
    $.get("/api/v1.0/areas", function(resp){
        if (resp.errno == "0"){
            var areas = resp.data;
            // 使用循环添加标签
            // for (i=0; i<areas.length; i++){
            //     var area = areas[i];
            //     $('#area-id').append('<option value="' + area.aid + '">' + area.aname +'</option>');
            // }
            
            // 使用art_template模板
            var html = template("areas-tmpl", {areas: areas});
            $("#area-id").html(html);
        }
    })

    // 新房屋信息上传表单
    $("#form-house-info").submit(function(e){
        // 1. 阻止默认事件
        e.preventDefault();
        
        // 2. 处理表单数据
        var data = {};
        $("#form-house-info").serializeArray().map(function(x){ data[x.name]=x.value });

        // 3. 收集设施id
        var facility = [];
        $(":checked[name=facility]").each(function(index, x){ facility[index]=$(x).val() });
        data.facility = facility;

        // 4. 向后端发送请求
        $.ajax({
            url: "/api/v1.0/houses/info",
            type: "post",
            contentType: "application/json",
            data: JSON.stringify(data),
            dataType: "json",
            headers: {"X-CSRFToken": getCookie("csrf_token")},
            success: function(resp){
                if (resp.errno == "4101"){
                    // 用户未登录
                    location.href = "/login.html"
                }
                else if (resp.errno == "0"){
                    // 上传成功，隐藏信息表单，显示上传图片表单
                    $("#form-house-info").hide();
                    $("#form-house-image").show();
                    // 设置图片表单种的house_id字段
                    $('#house-id').val(resp.data.house_id);
                } 
                else {
                    
                }
            }
        })

    });

    // 新房屋图片上传表单
    $("#form-house-image").submit(function(e){
        alert('bbbb');
        // 1. 阻止默认事件发生
        e.preventDefault();
        $(this).ajaxSubmit({
            url: "/api/v1.0/houses/image",
            type: "post",
            dataType: "json",
            headers: {"X-CSRFToken": getCookie("csrf_token")},
            success: function(resp){
                if (resp.errno == "4101"){
                    // 未登录
                    location.href = "login.html";
                }
                else if (resp.errno == "0"){
                    $(".house-image-cons").append("<img src='" + resp.data.image_url + "'>");
                }
                else {
                    alert(resp.data.errmsg);
                }
            }
        })
    })    

})