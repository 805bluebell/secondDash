// Modify title
document.title = "Live Posts";

//Date picker
$(function() {
    $("#fromdatepicker").datepicker({ dateFormat: "dd-mm-yy" });
});
$(function() {
    $("#todatepicker").datepicker({ dateFormat: "dd-mm-yy" });
});

//Ajax call to load the bigDict
$(document).ready(function() {
    // Hiding table &b funnel
    // $("example-table").hide();
    // $("chartdivs").hide();

    $.ajax({
        type: "GET",
        cache: true,
        url: "/getDropdownOptionsLive",
        data: "", //ajax parameters
        success: function(result) {
            myNestedVals = result;

            // Generating multiselect pillbox of select2
            $("#ddl1").select2();
            $("#ddl2").select2();
            $("#ddl3").select2();
            $("#profileArchiveStatus").select2();
            $("#customFilterDD").select2();
        }
    });
});

//Code inspired from http://benalexkeen.com/auto-updating-dropdown-fields-in-javascript/
function createOption(ddl, text, value) {
    var opt = document.createElement("option");
    opt.value = value;
    opt.text = text;
    ddl.options.add(opt);
}

function createOptions(optionsArray, ddl) {
    optionsArray.sort();
    for (i = 0; i < optionsArray.length; i++) {
        createOption(ddl, optionsArray[i], optionsArray[i]);
    }
}

function configureDDL2(ddl1, ddl2, ddl3) {
    ddl2.options.length = 0;
    ddl3.options.length = 0;
    createOption(ddl2, "Choose", "nothing");

    // Flushing out the selected option & recreating the select2 dropdown
    $("#ddl2").select2("destroy");
    $("#ddl2").select2();

    $("#ddl3")
        .select2()
        .val(null)
        .trigger("change");

    var ddl2keys = Object.keys(myNestedVals[ddl1.value]);
    createOptions(ddl2keys, ddl2);
}

function configureDDL3(ddl1, ddl2, ddl3) {
    ddl3.options.length = 0;
    createOption(ddl3, "All", "All");

    // Refreshing dropdowns to flush old selections
    $("#ddl3")
        .select2()
        .val(null)
        .trigger("change");

    $("#ddl3").val("All");
    $("#ddl3").trigger("change");

    var ddl3keys = myNestedVals[ddl1.value][ddl2.value];
    createOptions(ddl3keys, ddl3);
}

$("#sendForTable").on("click", function(e) {
    document.getElementById("example-table").style.display = "flex";
    document.getElementById("chartdivs").style.display = "none";
    document.getElementById("nobodyFound").style.display = "none";
    document.getElementById("toggleCollapse").style.display = "flex";
    e.preventDefault();
    var x = getFormData($("#bigForm"));

    // Nested calculator of TOTAL for each posting
    var nestedCalc = function(values, data, calcParams) {
        var calc = 0;

        data.forEach(function(row) {
            for (let i = 0; i < row._children.length; i++) {
                calc += row._children[i][calcParams.field];
            }
        });

        return calc;
    };

    // Rewriting the heading of Posting name
    var customGroupHeader = function(value, count, data, group) {
        return value + "<span style='color:#d00; margin-left:10px;'></span>";
    };


    $.ajax({
        type: "POST",
        cache: false,
        url: "/getPipelineTable",
        data: {
            companyName: document.getElementById("ddl1").value,
            postingTeam: document.getElementById("ddl2").value,
            postingTitle: $("#ddl3").val(),
            postingArchiveStatus: "",
            profileArchiveStatus: document.getElementById("profileArchiveStatus")
                .value,
            from: document.getElementById("fromdatepicker").value,
            to: document.getElementById("todatepicker").value,
            requestType: "live",
            recruiter: "All"
        }, // multiple data sent using ajax
        success: function(result) {

            $(document).on("click", "#download-xl", downXL);
            $(document).on("click", "#download-PDF", downPDF);
            $(document).on("click", "#toggleCollapse", collapseToggler);

            function downXL() {
                JSONToCSVConvertor(result, "TAT Report");
            }

            function downPDF() {
                JSONToPDFConvertor(result, "TAT Report");
            }

            function collapseToggler() {
                traverseRows();
            }

            function isItAllZero(jso) {
                if (jso.length <= 0) {
                    return true;
                } else {
                    return false;
                }
            }




            var whoAreTheseCandidates = (cell, formatterParams) => {
                var data = cell.getData();
                if (cell.getValue() === undefined) {
                    return
                } else {
                    let e = document.getElementById("profileArchiveStatus");
                    let profileSelection = e.options[e.selectedIndex].value;
                    return "<a style='text-decoration:none; color:inherit;' target='_blank' href='https://tatreports.directi.com/elaborateHomepageCandidates?postingId=" + data['posting_id'] + "&origin=" + data['title'] + "&stage=" + formatterParams + "&profileStatus=" + profileSelection + "&fromDate=" + document.getElementById("fromdatepicker").value + "&toDate=" + document.getElementById("todatepicker").value + "'>" + cell.getValue() + "</a>";
                }
            }

            if (isItAllZero(result)) {
                // Place a message
                document.getElementById("example-table").style.display = "none";
                document.getElementById("nobodyFound").style.display = "flex";
            } else {
                // Display the table
                // Creating a Tabulator object

                table = new Tabulator("#example-table", {
                    data: result,
                    height: "75vh",
                    layout: "fitColumns",
                    placeholder: "No Data",
                    dataTree: true,
                    dataTreeStartExpanded: false,
                    groupHeader: customGroupHeader,
                    tooltips: function(cell) {
                        const countOf_phoneToOnsiteCount = cell.getRow().getData()
                            .phoneToOnsiteCount;
                        const countOf_phoneToOfferCount = cell.getRow().getData()
                            .phoneToOfferCount;
                        const countOf_onsiteToOfferCount = cell.getRow().getData()
                            .onsiteToOfferCount;

                        if (cell.getColumn().getField() == "onsiteInterviewCount") {
                            return countOf_phoneToOnsiteCount ?
                                "Phone to Onsite: " + countOf_phoneToOnsiteCount :
                                "";
                        }

                        if (cell.getColumn().getField() == "offerCount") {
                            let temp = countOf_phoneToOfferCount ?
                                "Phone to Offer: " + countOf_phoneToOfferCount :
                                "";
                            temp = countOf_onsiteToOfferCount ?
                                (temp += "\nOnsite to Offer: " + countOf_onsiteToOfferCount) :
                                (temp += "\n");
                            return temp;
                        }
                    },
                    columns: [
                        { title: "Posting", field: "title", width: 290, responsive: 0 },
                        {
                            title: "New Lead",
                            field: "newLeadCount",
                            width: 100,
                            bottomCalc: nestedCalc,
                            bottomCalcParams: { field: "newLeadCount" },
                            formatter: whoAreTheseCandidates,
                            formatterParams: "newLead"
                        },
                        {
                            title: "Reached Out",
                            field: "reachedOutCount",
                            width: 100,
                            bottomCalc: nestedCalc,
                            bottomCalcParams: { field: "reachedOutCount" },
                            formatter: whoAreTheseCandidates,
                            formatterParams: "reachedOut"
                        },
                        {
                            title: "New applicant",
                            field: "newApplicantCount",
                            width: 100,
                            bottomCalc: nestedCalc,
                            bottomCalcParams: { field: "newApplicantCount" },
                            formatter: whoAreTheseCandidates,
                            formatterParams: "newApplicant"
                        },
                        {
                            title: "Recruiter Screen",
                            field: "recruiterScreenCount",
                            width: 100,
                            bottomCalc: nestedCalc,
                            bottomCalcParams: { field: "recruiterScreenCount" },
                            formatter: whoAreTheseCandidates,
                            formatterParams: "recruiterScreen"
                        },
                        {
                            title: "Phone Interview",
                            field: "phoneInterviewCount",
                            width: 100,
                            bottomCalc: nestedCalc,
                            bottomCalcParams: { field: "phoneInterviewCount" },
                            formatter: whoAreTheseCandidates,
                            formatterParams: "phoneInterview"
                        },
                        {
                            title: "On-site",
                            field: "onsiteInterviewCount",
                            width: 100,
                            bottomCalc: nestedCalc,
                            bottomCalcParams: { field: "onsiteInterviewCount" },
                            formatter: whoAreTheseCandidates,
                            formatterParams: "onsiteInterview"
                        },
                        {
                            title: "Offer",
                            field: "offerCount",
                            width: 100,
                            bottomCalc: nestedCalc,
                            bottomCalcParams: { field: "offerCount" },
                            formatter: whoAreTheseCandidates,
                            formatterParams: "offer"
                        },
                        {
                            title: "Hired",
                            field: "hiredCount",
                            width: 90,
                            bottomCalc: nestedCalc,
                            bottomCalcParams: { field: "hiredCount" },
                            formatter: whoAreTheseCandidates,
                            formatterParams: "hired"
                        },
                        {
                            title: "posting_id",
                            field: "posting_id",
                            width: 0.5,
                            visible: false,
                            formatter: function(cell, formatterParams) {
                                if (cell.getData()["topTag"] == "true") {
                                    //cell.getRow().getElement().style.fontWeight = "bold";
                                    cell.getRow().getElement().style.backgroundColor = "#C0C0C0";
                                    cell.getRow().getElement().style.color = "#000000";
                                }
                            }
                        }
                    ],

                    footerElement: "<button id='download-xl'>Download Excel</button><button id='download-PDF'>Download PDF</button>"
                });
            }
        }
    });

    function getFormData($form) {
        var unindexed_array = $form.serializeArray();
        var indexed_array = {};

        $.map(unindexed_array, function(n, i) {
            indexed_array[n["name"]] = n["value"];
        });

        return indexed_array;
    }
});

// The funnel script here
$("#sendForFunnel").on("click", function(e) {
    document.getElementById("example-table").style.display = "none";
    document.getElementById("chartdivs").style.display = "flex";
    document.getElementById("nobodyFound").style.display = "none";
    e.preventDefault();
    var x = getFormData($("#bigForm"));

    // Clearing all funnels drawn, if any. https://stackoverflow.com/questions/3955229/remove-all-child-elements-of-a-dom-node-in-javascript
    var myNode = document.getElementById("chartdivs");
    while (myNode.firstChild) {
        myNode.removeChild(myNode.firstChild);
    }

    $.ajax({
        type: "POST",
        cache: false,
        url: "/getPipelineTable",
        data: {
            companyName: document.getElementById("ddl1").value,
            postingTeam: document.getElementById("ddl2").value,
            postingTitle: $("#ddl3").val(),
            postingArchiveStatus: "",
            profileArchiveStatus: document.getElementById("profileArchiveStatus")
                .value,
            from: document.getElementById("fromdatepicker").value,
            to: document.getElementById("todatepicker").value,
            requestType: "live",
            recruiter: "All"
        }, //ajax parameters
        success: function(result) {
            function isItAllZero(jso) {
                if (jso.length <= 0) {
                    return true;
                } else {
                    return false;
                }
            }

            if (isItAllZero(result)) {
                // Place a message
                document.getElementById("example-table").style.display = "none";
                document.getElementById("chartdivs").style.display = "none";
                document.getElementById("nobodyFound").style.display = "flex";
            } else {
                for (let i = 0; i < result.length; i++) {
                    chartVar = "chartdiv";
                    chartVar += i.toString();
                    $("#chartdivs").append(
                        `<div style="text-align:center; margin:auto"><b>${result[i]["title"]}</b><br><div  id=${chartVar}></div></div>`
                    );

                    let var1 = 0,
                        var2 = 0,
                        var3 = 0,
                        var4 = 0,
                        var5 = 0,
                        var6 = 0,
                        var7 = 0,
                        var8 = 0;

                    for (let j = 0; j < result[i]["_children"].length; j++) {
                        if (result[i]["_children"][j]["title"] == "Total") {
                            continue;
                        }
                        var1 += result[i]["_children"][j]["newLeadCount"];
                        var2 += result[i]["_children"][j]["reachedOutCount"];
                        var3 += result[i]["_children"][j]["newApplicantCount"];
                        var4 += result[i]["_children"][j]["recruiterScreenCount"];
                        var5 += result[i]["_children"][j]["phoneInterviewCount"];
                        var6 += result[i]["_children"][j]["onsiteInterviewCount"];
                        var7 += result[i]["_children"][j]["offerCount"];
                        var8 += result[i]["_children"][j]["hiredCount"];
                    }

                    trigger(chartVar, var1, var2, var3, var4, var5, var6, var7, var8);
                }
            }
        }
    });

    function getFormData($form) {
        var unindexed_array = $form.serializeArray();
        var indexed_array = {};

        $.map(unindexed_array, function(n, i) {
            indexed_array[n["name"]] = n["value"];
        });

        return indexed_array;
    }
});