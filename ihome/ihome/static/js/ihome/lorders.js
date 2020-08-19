//模态框居中的控制
function centerModals(){
    $('.modal').each(function(i){   //遍历每一个模态框
        var $clone = $(this).clone().css('display', 'block').appendTo('body');    
        var top = Math.round(($clone.height() - $clone.find('.modal-content').height()) / 2);
        top = top > 0 ? top : 0;
        $clone.remove();
        $(this).find('.modal-content').css("margin-top", top-30);  //修正原先已经有的30个像素
    });
}

function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(document).ready(function(){
    $('.modal').on('show.bs.modal', centerModals);      //当模态框出现的时候
    $(window).on('resize', centerModals);

    // 房东查询自己的房子订单
    $.get("/api/v1.0/user/orders?role=landlord", function(resp){
        if (resp.errno == "0"){
            // 给模板传递参数
            $(".orders-list").html(template("orders-list-tmpl", {orders:resp.data.orders}))

            // 点击接单按钮
            $(".order-accept").on("click", function(){
                // 给接受框添加order-id属性
                var orderId = $(this).parents("li").attr("order-id");
                $(".modal-accept").attr("order-id", orderId);
            });
            // 确认接单处理
            $(".modal-accept").on("click", function(){
                var orderId = $(this).attr("order-id");
                $.ajax({
                    url:"/api/v1.0/orders/"+orderId+"/status",
                    type:"PUT",
                    contentType:"application/json",
                    data:'{"action":"accept"}',         // 传递参数action标识接单/拒单
                    dataType:"json",
                    headers:{"X-CSRFToken":getCookie("csrf_token")},
                    success:function(resp){
                        if (resp.errno == "4101"){
                            location.href = "/login.html";
                        }
                        else if (resp.errno == "0"){
                            $(".orders-list>li[order-id="+ orderId +"]>div.order-content>div.order-text>ul li:eq(4)>span").html("已接单");
                            $("ul.orders-list>li[order-id="+ orderId +"]>div.order-title>div.order-operate").hide();
                            $("#accept-modal").modal("hide");
                        }
                    }
                })
            })

            // 点击拒单按钮
            $(".order-reject").on("click", function(){
                // 给拒单框添加order-id属性
                var orderId = $(this).parents("li").attr("order-id");
                $(".modal-reject").attr("order-id", orderId);
            })
            // 拒单处理
            $(".modal-reject").on("click", function(){
                // 获取orderId, 拒单理由
                var orderId = $(this).attr("order-id");
                var reject_reason = $("#reject-reason").val();
                if (!reject_reason) return;
                // 组织传递参数
                var data = {
                    action:"reject",
                    reason:reject_reason
                };
                // 发起ajax请求
                $.ajax({
                    url:"/api/v1.0/orders/"+orderId+"/status",
                    type:"PUT",
                    data:JSON.stringify(data),
                    contentType:"application/json",
                    dataType:"json",
                    headers:{"X-CSRFToken":getCookie("csrf_token")},
                    success:function(resp){
                        if (resp.errno == "4101"){
                            location.href = "/login.html";
                        }
                        else if(resp.error == "0"){
                            $(".orders-list>li[order-id="+ orderId +"]>div.order-content>div.order-text>ul li:eq(4)>span").html("已拒单");
                            $("ul.orders-list>li[order-id="+ orderId +"]>div.order-title>div.order-operate").hide();
                            $("#reject-modal").modal("hide");
                        }
                    }
                })

            })

        }
    })




    $(".order-accept").on("click", function(){
        var orderId = $(this).parents("li").attr("order-id");
        $(".modal-accept").attr("order-id", orderId);
    });
    $(".order-reject").on("click", function(){
        var orderId = $(this).parents("li").attr("order-id");
        $(".modal-reject").attr("order-id", orderId);
    });
});