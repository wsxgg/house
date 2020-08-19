function hrefBack() {
    history.go(-1);
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

// 获取cookie
function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(document).ready(function(){
    // 获取详情页面的编号
    var queryData = decodeQuery();
    var houseId = queryData['id'];

    // 获取该房屋的详细信息
    $.get("/api/v1.0/houses/"+houseId, function(resp){
        if (resp.errno == "0"){
            // 渲染详情页上方幻灯片
            $(".swiper-container").html(template("house-image-tmpl", {img_urls:resp.data.house.img_urls, price:resp.data.house.price}));
            // 渲染下方详细信息
            $(".detail-con").html(template("house-detail-tmpl", {house:resp.data.house}));

            // 判断是否是房东，从而显示或隐藏预约按钮
            if (resp.data.user_id != resp.data.house.user_id){
                // 如果不是房东，显示预约按钮，隐藏修改
                $(".booking").attr("href", "/booking.html?hid="+resp.data.house.hid);
                $('.booking').show();
                $(".change").hide();
                $(".delete").hide();
            }
            else {
                // 如果是房东，显示修改，隐藏预约
                $(".change").attr("href", "/changehouse.html?hid="+resp.data.house.hid);
                $('.change').show();
                $('.delete').show();
                $(".booking").hide();
            }
            var mySwiper = new Swiper ('.swiper-container', {
                loop: true,
                autoplay: 2000,
                autoplayDisableOnInteraction: false,
                pagination: '.swiper-pagination',
                paginationType: 'fraction'
            })
            // 点击删除
            // 由data-target="#delete-modal"实现弹框

            // 确认删除
            $('.modal-delete').on("click", function(){
                // 开始已经获取过houseId
                // 发送ajax请求
                $.ajax({
                    url:"/api/v1.0/houses/"+houseId+"/delete",
                    type:"put",
                    contentType:"application/json",
                    dataType:"json",
                    headers:{"X-CSRFToken":getCookie("csrf_token")},
                    success:function(resp){
                        if (resp.errno == "4101"){
                            location.href = "/login.html";
                        }
                        else if (resp.errno == "0"){
                            alert("删除成功");
                            location.href = '/myhouse.html';
                        }
                        else {
                            alert(resp.errmsg);
                        }
                    }
                })

            })

        }
    })
})