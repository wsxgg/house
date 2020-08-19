// 全局声明页码
var cur_page = 1;   // 当前页
var next_page = 1;   // 下一页
var total_page = 1;     //总页数
var house_data_querying = true;     // 是否正在向后台获取数据


function decodeQuery(){
    var search = decodeURI(document.location.search);
    return search.replace(/(^\?)/, '').split('&').reduce(function(result, item){
        values = item.split('=');
        result[values[0]] = values[1];
        return result;
    }, {});
}

// 更新用户点击的筛选条件函数
function updateFilterDateDisplay() {
    var startDate = $("#start-date").val();
    var endDate = $("#end-date").val();
    var $filterDateTitle = $(".filter-title-bar>.filter-title").eq(0).children("span").eq(0);
    if (startDate) {
        var text = startDate.substr(5) + "/" + endDate.substr(5);
        $filterDateTitle.html(text);
    } else {
        $filterDateTitle.html("入住日期");
    }
}


// 因为在搜索页面，没更改一次搜索选项，都是向后端的一次访问，很频繁，所以这边单独创建一个函数
// 创建向后端请求的函数
function updateHouseData(action){
    // 获取选择的areaId
    var areaId = $(".filter-area>li.active").attr("area-id");
    if (areaId == undefined){
        areaId = "";
    }
    // 获取起始时间,结束时间,排序方式
    var startDate = $("#start-date").val();
    var endDate = $("#end-date").val();
    var sortKey = $(".filter-sort>li.active").attr("sort-key");
    // 组织ajax参数
    var params = {
        aid:areaId,
        sd:startDate,
        ed:endDate,
        sk:sortKey,
        p:next_page
    }
    // 向后端发送ajax请求
    $.get("/api/v1.0/houses", params, function(resp){
        house_data_querying = false;
        if (resp.errno == "0"){
            if (resp.data.total_page == 0){
                $('.house-list').html("暂时没有符合您查询的房屋信息");
            }
            else{
                total_page = resp.data.total_page;
                if (action == "renew"){     // action为该函数的一个参数，在调用时指定
                    // 如果刷新条件时
                    cur_page = 1;
                    $('.house-list').html(template("house-list-tmpl", {houses:resp.data.houses}));
                }
                else{
                    cur_page = next_page;
                    $('.house-list').append(template("house-list-tmpl", {houses:resp.data.houses}));
                }
            }
        }
    })

}


$(document).ready(function(){
    // 1. 页面加载好，首先获取主页搜索传递的参数信息
    var queryData = decodeQuery();
    var startDate = queryData["sd"];
    var endDate = queryData["ed"];
    $("#start-date").val(startDate); 
    $("#end-date").val(endDate);
    updateFilterDateDisplay();
    var areaName = queryData["aname"];
    if (!areaName) areaName = "位置区域";
    $(".filter-title-bar>.filter-title").eq(1).children("span").eq(0).html(areaName);

    // 2. 向后端获取区域名的请求
    $.get("/api/v1.0/areas", function(data){
        if (data.errno == "0"){
            // 用户首页搜索过来，可能已经选择了城区
            var areaId = queryData["aid"];
            // 遍历请求的areas数据
            if (areaId) {
                // 从url获取的areaId是str，而从后端获取的id是int，所以需要转换
                areaId = parseInt(areaId);
                for (var i=0; i<data.data.length; i++) {
                    if (data.data[i].aid == areaId){
                        $(".filter-area").append('<li area-id="'+data.data[i].aid+'" class="active" >'+data.data[i].aname+'</li>');
                    }
                    else{
                        $(".filter-area").append('<li area-id="'+data.data[i].aid+'">'+data.data[i].aname+'</li>');
                    }
                }
            }
            else{
                for (var i=0; i<data.data.length; i++){
                    $(".filter-area").append('<li area-id="'+data.data[i].aid+'">'+data.data[i].aname+'</li>');
                }
            }
        }
    })

    // 3. 调用一次刷新请求
    updateHouseData("renew");

    // 4. 页面滚动进行翻页
    // 获取页面显示窗口的高度
    var windowHeight = $(window).height();
    // 为窗口的滚动添加事件函数
    window.onscroll=function(){
         // var a = document.documentElement.scrollTop==0? document.body.clientHeight : document.documentElement.clientHeight;
         var b = document.documentElement.scrollTop==0? document.body.scrollTop : document.documentElement.scrollTop;
         var c = document.documentElement.scrollTop==0? document.body.scrollHeight : document.documentElement.scrollHeight;
         // 如果滚动到接近窗口底部
         if(c-b<windowHeight+50){
             // 如果没有正在向后端发送查询房屋列表信息的请求
             if (!house_data_querying) {
                 // 将正在向后端查询房屋列表信息的标志设置为真，
                 house_data_querying = true;
                 // 如果当前页面数还没到达总页数
                 if(cur_page < total_page) {
                     // 将要查询的页数设置为当前页数加1
                     next_page = cur_page + 1;
                     // 向后端发送请求，查询下一页房屋数据
                     updateHouseData();
                 } else {
                     house_data_querying = false;
                 }
             }
         }
    }

    // 5. 修改筛选条件
    // 当用户更新筛选条件完成后（即点击下方阴影框时）执行条件更新函数,初始化页码，重新提交请求函数
    $(".display-mask").on("click", function(e) {
        $(this).hide();
        $filterItem.removeClass('active');
        updateFilterDateDisplay();
        cur_page = 1;
        next_page = 1;
        total_page = 1;
        updateHouseData("renew")

    });


    $(".input-daterange").datepicker({
        format: "yyyy-mm-dd",
        startDate: "today",
        language: "zh-CN",
        autoclose: true
    });
    var $filterItem = $(".filter-item-bar>.filter-item");
    $(".filter-title-bar").on("click", ".filter-title", function(e){
        var index = $(this).index();
        if (!$filterItem.eq(index).hasClass("active")) {
            $(this).children("span").children("i").removeClass("fa-angle-down").addClass("fa-angle-up");
            $(this).siblings(".filter-title").children("span").children("i").removeClass("fa-angle-up").addClass("fa-angle-down");
            $filterItem.eq(index).addClass("active").siblings(".filter-item").removeClass("active");
            $(".display-mask").show();
        } else {
            $(this).children("span").children("i").removeClass("fa-angle-up").addClass("fa-angle-down");
            $filterItem.eq(index).removeClass('active');
            $(".display-mask").hide();
            updateFilterDateDisplay();
        }
    });



    $(".filter-item-bar>.filter-area").on("click", "li", function(e) {
        if (!$(this).hasClass("active")) {
            $(this).addClass("active");
            $(this).siblings("li").removeClass("active");
            $(".filter-title-bar>.filter-title").eq(1).children("span").eq(0).html($(this).html());
        } else {
            $(this).removeClass("active");
            $(".filter-title-bar>.filter-title").eq(1).children("span").eq(0).html("位置区域");
        }
    });
    $(".filter-item-bar>.filter-sort").on("click", "li", function(e) {
        if (!$(this).hasClass("active")) {
            $(this).addClass("active");
            $(this).siblings("li").removeClass("active");
            $(".filter-title-bar>.filter-title").eq(2).children("span").eq(0).html($(this).html());
        }
    })

})