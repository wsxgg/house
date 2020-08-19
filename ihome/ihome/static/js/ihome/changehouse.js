function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

// 获取url上的参数
function decodeQuery(){
    var search = decodeURI(document.location.search);
    return search.replace(/(^\?)/, '').split('&').reduce(function(result, item){
        values = item.split('=');
        result[values[0]] = values[1];
        return result;
    }, {});
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
    });

    // 获取详情页面的编号
    var queryData = decodeQuery();
    var houseId = queryData['hid'];
    // 像后端获取房屋信息
    $.getJSON("/api/v1.0/houses/"+houseId+"/change", function(resp){
        if (resp.errno == "4101"){
            location.href = "/login.html";
        }
        else if (resp.errno == "0"){
            // 将房屋信息自动填充到表单
            for ( value in resp.data.house){
                key = "resp.data.house."+value;
                $("[name="+value+"]").val(eval(key));  
            }
            // 将该房屋的设施自动勾选
            for ( i in resp.data.house.facilities ){
                $("[value="+resp.data.house.facilities[i]+"]").prop("checked", true);
            }
        }
    })

    // 再上传修改之前记得附带house_id
    // 新房屋信息更改后上传表单
    $("#form-house-info").submit(function(e){
        // 1. 阻止默认事件
        e.preventDefault();
        
        // 2. 处理表单数据
        var data = {};
        data['house_id'] = houseId;
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
                    // 获取图片链接（如果有的话）
                    for ( img_url in resp.data.images ){
                        $(".house-image-cons").append("<img src='" + resp.data.images[img_url] + "'>");
                    }

                } 
            }
        })

    });

    // 新房屋图片上传表单
    $("#form-house-image").submit(function(e){
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