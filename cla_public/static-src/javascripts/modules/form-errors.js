(function () {
  'use strict';

  moj.Modules.FormErrors = {
    init: function() {
      this.bindEvents();
      this.loadTemplates();
    },

    bindEvents: function() {
      $('button[type="submit"]', $('form')).on('click',  $.proxy(this.postToFormErrors, this));
    },

    postToFormErrors: function(e) {
      this.$form = $(e.currentTarget).closest('form');
      if (this.$form.length) {
        e.preventDefault();
        e.stopPropagation();
        $.ajax({
          type: 'OPTIONS',
          url: '',
          contentType: 'application/x-www-form-urlencoded',
          data: this.$form.serialize()
        }).done(
          $.proxy(this.onAjaxSuccess, this)
        ).fail(
          $.proxy(this.onAjaxError, this)
        );
      }
    },

    onAjaxSuccess: function (errors) {
      if (!$.isEmptyObject(errors)) {
        this.loadErrors(errors);
        $('html, body').animate({
            scrollTop: $('.alert-error:visible:first').offset().top - 50
        }, 300);
      } else {
        this.$form.submit();
      }
    },

    onAjaxError: function () {
      this.$form.submit();
    },

    formatErrors: function (errors) {
      var errorFields = {};

      (function fieldName (errorsObj, prefix) {
        prefix = (typeof prefix === 'undefined')? '': prefix + '-';
        for (var key in errorsObj) {
          var field = prefix + key;
          if ($.isArray(errorsObj[key])) {
            errorFields[field] = errorsObj[key];
          } else {
            fieldName(errorsObj[key], field);
          }
        }
      })(errors);

      return errorFields;
    },

    loadErrors: function (errors) {
      var errorFields = this.formatErrors(errors);

      for (var id in errorFields) {
        $('#field-' + id).addClass('m-error');

        var $labelElement = $('#field-label-' + id);
        $labelElement.addClass('m-error');

        var $fieldErrors = $('<div class="form-row field-error"/>');

        for (var i = 0; i <  errorFields[id].length; i++ ) {
          $fieldErrors.append($('<p/>').text(errorFields[id][i]));
        }

        $labelElement.after($fieldErrors);
      }

      this.$form.prepend(this.mainFormError);
    },

    loadTemplates: function () {
      this.mainFormError = _.template($('#mainFormError').html());
    }
  };
}());
