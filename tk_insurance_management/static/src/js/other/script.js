/** @odoo-module **/
import { rpc } from "@web/core/network/rpc";

$(document).ready(function () {
    //Insurance Sub Category
    $("#insurance_category_id").on("change", function () {
        var text = "<option value='' selected='selected'>Select Sub Category</option>"
        var categoryId = $(this).val();
        rpc("/get_category_wise_sub_category", {
            insurance_category_id: categoryId
        }).then(function (sub_category) {
            if (sub_category) {
                for (var key in sub_category) {
                    text = text + '<option value="' + key + '">' + sub_category[key] + '</option>'
                }
            }
            $('#insurance_sub_category_id').empty().append(text);
        });
    });

    // Age Count
    $('#policy_holder_dob').on('change', function () {
        let dateOfBirth = $('#policy_holder_dob').val();
        let today = new Date();
        let birthDate = new Date(dateOfBirth);
        let age = today.getFullYear() - birthDate.getFullYear();
        let monthDiff = today.getMonth() - birthDate.getMonth();
        let dayDiff = today.getDate() - birthDate.getDate();
        if (monthDiff < 0 || (monthDiff === 0 && dayDiff < 0)) {
            age--;
        }
        if (birthDate >= today) {
            $('#policy_holder_age').val('');
            $('#age_alert').empty().append(`
            <div class="alert alert-warning alert-dismissible fade show" role="alert">
                Date of Birth should be earlier than today's date.
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `);
            $('.text-end button[type="submit"]').hide();  // Hide submit button
        } else {
            $('#age_alert').empty();
            $('#policy_holder_age').val(age);
            $('.text-end button[type="submit"]').show();  // Show submit button
        }
    });


    // Claim Date Check
    $('#claim_date').on('change', function () {
        let claimDate = new Date($(this).val());
        let issueDate = new Date($('input[name="issue_date"]').val());
        let expiryDate = new Date($('input[name="expiry_date"]').val());

        $('#claim_date_alert').remove();

        // Validate
        if (claimDate < issueDate || claimDate > expiryDate) {
            $(this).after(`
            <div id="claim_date_alert" class="alert alert-danger alert-dismissible fade show text-center mt-1" role="alert">
                Claim Date must be between Insurance Issue Date and Expiry Date.
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `);
            $('.modal-footer button[type="submit"]').prop('disabled', true);
        } else {
            $('.modal-footer button[type="submit"]').prop('disabled', false);
        }
    });


    //   Reinsurance Check Before Claim Submit
    $('#submit_claim_form').on('submit', function (e) {
        const form = $(this);
        const isReinsuranceRequired = form.data('is-reinsurance-required') === true || form.data('is-reinsurance-required') === 'True';
        const reInsuranceId = form.data('re-insurance-id');
        const reInsuranceStatus = form.data('re-insurance-status');

        $('#reinsurance_alert').remove();

        if (isReinsuranceRequired) {
            if (!reInsuranceId) {
                e.preventDefault();
                form.prepend(`
                    <div id="reinsurance_alert" class="alert alert-warning alert-dismissible fade show text-center m-1" role="alert">
                        You cannot create the claim. Please contact the administrator to first create the reinsurance. Only then will you be able to create the claim.
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>
                `);
                return false;
            }
            if (reInsuranceStatus === 'draft') {
                e.preventDefault();
                form.prepend(`
                    <div id="reinsurance_alert" class="alert alert-warning alert-dismissible fade show text-center m-1" role="alert">
                        You cannot create the claim. Please ask the administrator to set the reinsurance status to 'Running' before proceeding
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>
                `);
                return false;
            }
        }
    });

});