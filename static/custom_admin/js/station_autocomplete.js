(function($) {
    'use strict';
    $(function() {
        // Initialize enhanced station select
        function initStationSelect() {
            $('.field-start_station select, .field-end_station select').each(function() {
                $(this).select2({
                    ajax: {
                        delay: 250,
                        data: function(params) {
                            return {
                                term: params.term,
                                page: params.page
                            };
                        },
                        processResults: function(data, params) {
                            return {
                                results: data.results,
                                pagination: {
                                    more: data.pagination.more
                                }
                            };
                        }
                    },
                    templateResult: formatStation,
                    templateSelection: formatStationSelection,
                    escapeMarkup: function(markup) { return markup; }
                });
            });
        }

        // Format station in dropdown
        function formatStation(station) {
            if (!station.id) return station.text;
            return $('<div class="station-select2-result">' +
                    '<span class="station-select2-name">' + station.text + '</span>' +
                    '<span class="station-select2-lines">' + 
                    (station.lines ? station.lines : '') + '</span>' +
                    '</div>');
        }

        // Format selected station
        function formatStationSelection(station) {
            if (!station.id) return station.text;
            return $('<span class="station-select2-selection">' + 
                    station.text +
                    (station.lines ? ' (' + station.lines + ')' : '') +
                    '</span>');
        }

        // Initialize when document is ready
        $(document).ready(function() {
            initStationSelect();
        });

        // Initialize when adding inline forms
        $(document).on('formset:added', function(event, $row, formsetName) {
            initStationSelect();
        });
    });
})(django.jQuery);