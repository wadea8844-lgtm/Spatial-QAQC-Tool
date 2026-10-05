from qgis.PyQt.QtCore import QCoreApplication, QVariant, QDateTime
from qgis.PyQt.QtGui import QTextDocument
from qgis.PyQt.QtPrintSupport import QPrinter

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterNumber,
    QgsProcessingParameterCrs,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFileDestination,
    QgsProcessingException,
    QgsFeature,
    QgsField,
    QgsFields,
    QgsVariantUtils,
    QgsVectorLayer,
    QgsCoordinateReferenceSystem,
    QgsProject,
    QgsDistanceArea,
    QgsPointXY
)

import processing
import html


class SpatialQAQCValidator(QgsProcessingAlgorithm):

    INPUT = 'INPUT'
    X_FIELD = 'X_FIELD'
    Y_FIELD = 'Y_FIELD'
    REPORT_FIELDS = 'REPORT_FIELDS'

    COORD_CRS = 'COORD_CRS'
    DUP_TOLERANCE = 'DUP_TOLERANCE'

    MIN_X = 'MIN_X'
    MAX_X = 'MAX_X'
    MIN_Y = 'MIN_Y'
    MAX_Y = 'MAX_Y'

    OUTPUT = 'OUTPUT'
    EXCEL = 'EXCEL'
    PDF = 'PDF'


    # =========================================================
    # BASIC INFORMATION
    # =========================================================

    def tr(self, text):
        return QCoreApplication.translate(
            'Processing',
            text
        )


    def createInstance(self):
        return SpatialQAQCValidator()


    def name(self):
        return 'spatial_qaqc_validator'


    def displayName(self):
        return 'Spatial QA/QC Validator'


    def group(self):
        return 'QA/QC Tools'


    def groupId(self):
        return 'qaqc_tools'


    def shortHelpString(self):

        return """
        Spatial Data QA/QC Validator

        Checks:
        • Missing coordinates
        • Invalid coordinate values
        • Exact and near-duplicate locations
        • Coordinates outside valid extent
        • X/Y coordinate swaps

        Duplicate Detection:
        A user-defined distance tolerance in meters
        is used to detect records located very close
        to one another.

        X/Y Swap:
        X/Y values are automatically corrected only
        when the original coordinates fall outside
        the valid project extent and the swapped
        coordinates fall inside it.

        Outputs:
        • Validated QA/QC dataset
        • Excel file containing issue records only
        • Styled PDF QA/QC report
        """


    # =========================================================
    # PARAMETERS
    # =========================================================

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                'Input Table / Layer'
            )
        )


        self.addParameter(
            QgsProcessingParameterField(
                self.X_FIELD,
                'X Field',
                parentLayerParameterName=self.INPUT
            )
        )


        self.addParameter(
            QgsProcessingParameterField(
                self.Y_FIELD,
                'Y Field',
                parentLayerParameterName=self.INPUT
            )
        )


        self.addParameter(
            QgsProcessingParameterField(
                self.REPORT_FIELDS,
                'Fields to include in Excel / PDF',
                parentLayerParameterName=self.INPUT,
                allowMultiple=True,
                optional=True
            )
        )


        self.addParameter(
            QgsProcessingParameterCrs(
                self.COORD_CRS,
                'Coordinate CRS',
                defaultValue='EPSG:4326'
            )
        )


        self.addParameter(
            QgsProcessingParameterNumber(
                self.DUP_TOLERANCE,
                'Duplicate tolerance (meters)',
                type=QgsProcessingParameterNumber.Double,
                defaultValue=1.0,
                minValue=0.0
            )
        )


        self.addParameter(
            QgsProcessingParameterNumber(
                self.MIN_X,
                'Minimum X',
                type=QgsProcessingParameterNumber.Double,
                defaultValue=54.30
            )
        )


        self.addParameter(
            QgsProcessingParameterNumber(
                self.MAX_X,
                'Maximum X',
                type=QgsProcessingParameterNumber.Double,
                defaultValue=54.70
            )
        )


        self.addParameter(
            QgsProcessingParameterNumber(
                self.MIN_Y,
                'Minimum Y',
                type=QgsProcessingParameterNumber.Double,
                defaultValue=24.30
            )
        )


        self.addParameter(
            QgsProcessingParameterNumber(
                self.MAX_Y,
                'Maximum Y',
                type=QgsProcessingParameterNumber.Double,
                defaultValue=24.60
            )
        )


        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                'QA/QC Output'
            )
        )


        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.EXCEL,
                'Issues Excel',
                'Excel (*.xlsx)'
            )
        )


        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.PDF,
                'QA/QC PDF Report',
                'PDF (*.pdf)'
            )
        )


    # =========================================================
    # PROCESS
    # =========================================================

    def processAlgorithm(
        self,
        parameters,
        context,
        feedback
    ):

        # -----------------------------------------------------
        # INPUT
        # -----------------------------------------------------

        source = self.parameterAsSource(
            parameters,
            self.INPUT,
            context
        )

        if source is None:
            raise QgsProcessingException(
                'Invalid input layer.'
            )


        x_field = self.parameterAsString(
            parameters,
            self.X_FIELD,
            context
        )


        y_field = self.parameterAsString(
            parameters,
            self.Y_FIELD,
            context
        )


        report_fields = self.parameterAsFields(
            parameters,
            self.REPORT_FIELDS,
            context
        )


        coordinate_crs = self.parameterAsCrs(
            parameters,
            self.COORD_CRS,
            context
        )


        duplicate_tolerance = self.parameterAsDouble(
            parameters,
            self.DUP_TOLERANCE,
            context
        )


        min_x = self.parameterAsDouble(
            parameters,
            self.MIN_X,
            context
        )


        max_x = self.parameterAsDouble(
            parameters,
            self.MAX_X,
            context
        )


        min_y = self.parameterAsDouble(
            parameters,
            self.MIN_Y,
            context
        )


        max_y = self.parameterAsDouble(
            parameters,
            self.MAX_Y,
            context
        )


        excel_path = self.parameterAsFileOutput(
            parameters,
            self.EXCEL,
            context
        )


        pdf_path = self.parameterAsFileOutput(
            parameters,
            self.PDF,
            context
        )


        source_field_names = source.fields().names()


        # -----------------------------------------------------
        # VALIDATION
        # -----------------------------------------------------

        if x_field not in source_field_names:
            raise QgsProcessingException(
                'Selected X field does not exist.'
            )


        if y_field not in source_field_names:
            raise QgsProcessingException(
                'Selected Y field does not exist.'
            )


        if min_x >= max_x:
            raise QgsProcessingException(
                'Minimum X must be smaller than Maximum X.'
            )


        if min_y >= max_y:
            raise QgsProcessingException(
                'Minimum Y must be smaller than Maximum Y.'
            )


        # -----------------------------------------------------
        # DEFAULT REPORT FIELDS
        # -----------------------------------------------------

        if not report_fields:

            preferred_fields = [
                'asset_id',
                'asset_name',
                'category',
                'district'
            ]

            report_fields = [
                f
                for f in preferred_fields
                if f in source_field_names
            ]


        report_fields = list(
            dict.fromkeys(report_fields)
        )


        # =====================================================
        # DISTANCE ENGINE
        # =====================================================

        distance_engine = QgsDistanceArea()

        distance_engine.setSourceCrs(
            coordinate_crs,
            QgsProject.instance().transformContext()
        )

        distance_engine.setEllipsoid(
            'WGS84'
        )


        # =====================================================
        # QA FIELDS
        # =====================================================

        qa_definitions = [

            ('QA_STATUS', QVariant.String),

            ('QA_ISSUE', QVariant.String),

            ('QA_ACTION', QVariant.String),

            ('DUPLICATE_WITH', QVariant.String),

            ('DUP_DISTANCE_M', QVariant.Double),

            ('ORIGINAL_X', QVariant.Double),

            ('ORIGINAL_Y', QVariant.Double),

            ('CORRECTED_X', QVariant.Double),

            ('CORRECTED_Y', QVariant.Double)
        ]


        # =====================================================
        # MAIN OUTPUT
        # =====================================================

        output_fields = QgsFields(
            source.fields()
        )


        for name, field_type in qa_definitions:

            output_fields.append(
                QgsField(
                    name,
                    field_type
                )
            )


        sink, dest_id = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            output_fields,
            source.wkbType(),
            source.sourceCrs()
        )


        if sink is None:
            raise QgsProcessingException(
                'Could not create QA/QC output.'
            )


        # =====================================================
        # EXCEL ISSUE TABLE
        # =====================================================

        report_output_fields = QgsFields()


        for field_name in report_fields:

            index = source.fields().indexOf(
                field_name
            )

            if index >= 0:

                original_field = (
                    source.fields().field(
                        index
                    )
                )

                report_output_fields.append(
                    QgsField(
                        original_field.name(),
                        original_field.type(),
                        original_field.typeName(),
                        original_field.length(),
                        original_field.precision()
                    )
                )


        for name, field_type in qa_definitions:

            report_output_fields.append(
                QgsField(
                    name,
                    field_type
                )
            )


        issues_layer = QgsVectorLayer(
            'None',
            'QAQC_Issues',
            'memory'
        )


        issues_provider = (
            issues_layer.dataProvider()
        )


        issues_provider.addAttributes(
            list(report_output_fields)
        )


        issues_layer.updateFields()


        # =====================================================
        # FIELD INDEXES
        # =====================================================

        x_idx = source.fields().indexOf(
            x_field
        )

        y_idx = source.fields().indexOf(
            y_field
        )


        # =====================================================
        # COUNTERS
        # =====================================================

        total_count = 0

        pass_count = 0

        missing_count = 0

        duplicate_count = 0

        swapped_count = 0

        outside_count = 0

        invalid_count = 0


        # Store already validated locations
        validated_locations = []


        issue_records = []


        total_features = source.featureCount()

        current = 0


        # =====================================================
        # HELPERS
        # =====================================================

        def inside_extent(x, y):

            return (
                min_x <= x <= max_x
                and
                min_y <= y <= max_y
            )


        def calculate_distance(
            x1,
            y1,
            x2,
            y2
        ):

            try:

                p1 = QgsPointXY(
                    x1,
                    y1
                )

                p2 = QgsPointXY(
                    x2,
                    y2
                )

                return float(
                    distance_engine.measureLine(
                        p1,
                        p2
                    )
                )

            except Exception:

                return None


        def find_near_duplicate(
            x,
            y
        ):

            closest_id = None

            closest_distance = None


            for item in validated_locations:

                distance = calculate_distance(
                    x,
                    y,
                    item['x'],
                    item['y']
                )


                if distance is None:
                    continue


                if distance <= duplicate_tolerance:

                    if (
                        closest_distance is None
                        or
                        distance < closest_distance
                    ):

                        closest_distance = distance

                        closest_id = item[
                            'asset_id'
                        ]


            return (
                closest_id,
                closest_distance
            )


        # =====================================================
        # QA/QC LOOP
        # =====================================================

        for feature in source.getFeatures():

            if feedback.isCanceled():
                break


            current += 1

            total_count += 1


            if total_features > 0:

                feedback.setProgress(
                    int(
                        current
                        / total_features
                        * 100
                    )
                )


            output_attributes = list(
                feature.attributes()
            )


            x_val = feature[
                x_field
            ]

            y_val = feature[
                y_field
            ]


            if 'asset_id' in source_field_names:

                asset_id = str(
                    feature[
                        'asset_id'
                    ]
                )

            else:

                asset_id = str(
                    feature.id()
                )


            status = ''

            issue = ''

            action = ''

            duplicate_with = ''

            duplicate_distance = None

            original_x = None

            original_y = None

            corrected_x = None

            corrected_y = None


            # =================================================
            # MISSING
            # =================================================

            x_missing = (
                QgsVariantUtils.isNull(
                    x_val
                )
                or
                str(x_val).strip() == ''
            )


            y_missing = (
                QgsVariantUtils.isNull(
                    y_val
                )
                or
                str(y_val).strip() == ''
            )


            if x_missing or y_missing:

                status = 'ERROR'

                issue = (
                    'Missing Coordinate'
                )

                action = (
                    'Manual Review'
                )

                missing_count += 1


            else:

                # =============================================
                # NUMERIC VALIDATION
                # =============================================

                try:

                    x = float(
                        x_val
                    )

                    y = float(
                        y_val
                    )

                    original_x = x

                    original_y = y


                except Exception:

                    x = None

                    y = None


                    status = 'ERROR'

                    issue = (
                        'Invalid Coordinate Value'
                    )

                    action = (
                        'Manual Review'
                    )

                    invalid_count += 1


                if x is not None:

                    # =========================================
                    # DETERMINE VALID / SWAPPED / OUTSIDE
                    # =========================================

                    was_swapped = False


                    if inside_extent(
                        x,
                        y
                    ):

                        corrected_x = x

                        corrected_y = y


                    else:

                        swapped_x = y

                        swapped_y = x


                        if inside_extent(
                            swapped_x,
                            swapped_y
                        ):

                            was_swapped = True

                            corrected_x = (
                                swapped_x
                            )

                            corrected_y = (
                                swapped_y
                            )


                            # Correct X/Y in output
                            output_attributes[
                                x_idx
                            ] = corrected_x

                            output_attributes[
                                y_idx
                            ] = corrected_y


                            swapped_count += 1


                        else:

                            status = 'ERROR'

                            issue = (
                                'Outside Valid Extent'
                            )

                            action = (
                                'Manual Review'
                            )

                            outside_count += 1


                    # =========================================
                    # DUPLICATE CHECK
                    # Only if valid corrected position exists
                    # =========================================

                    if (
                        corrected_x is not None
                        and
                        corrected_y is not None
                    ):

                        duplicate_with, duplicate_distance = (
                            find_near_duplicate(
                                corrected_x,
                                corrected_y
                            )
                        )


                        if duplicate_with is not None:

                            status = 'WARNING'


                            if was_swapped:

                                issue = (
                                    'X/Y Swapped + '
                                    'Potential Duplicate'
                                )

                                action = (
                                    'Auto Corrected + '
                                    'Manual Review'
                                )

                            else:

                                issue = (
                                    'Potential Duplicate'
                                )

                                action = (
                                    'Manual Review'
                                )


                            duplicate_count += 1


                        else:

                            if was_swapped:

                                status = 'FIXED'

                                issue = (
                                    'X/Y Swapped'
                                )

                                action = (
                                    'Auto Corrected'
                                )


                            else:

                                status = 'PASS'

                                action = 'None'

                                pass_count += 1


                        # Store valid location for future checks
                        validated_locations.append({
                            'asset_id': asset_id,
                            'x': corrected_x,
                            'y': corrected_y
                        })


            # =================================================
            # QA VALUES
            # =================================================

            qa_values = [

                status,

                issue,

                action,

                duplicate_with,

                duplicate_distance,

                original_x,

                original_y,

                corrected_x,

                corrected_y
            ]


            output_attributes.extend(
                qa_values
            )


            # =================================================
            # MAIN OUTPUT FEATURE
            # =================================================

            output_feature = QgsFeature(
                output_fields
            )


            if feature.hasGeometry():

                output_feature.setGeometry(
                    feature.geometry()
                )


            output_feature.setAttributes(
                output_attributes
            )


            sink.addFeature(
                output_feature
            )


            # =================================================
            # ISSUE RECORDS ONLY
            # =================================================

            if status != 'PASS':

                selected_values = []


                for field_name in report_fields:

                    selected_values.append(
                        feature[
                            field_name
                        ]
                    )


                selected_values.extend(
                    qa_values
                )


                issue_feature = QgsFeature(
                    report_output_fields
                )


                issue_feature.setAttributes(
                    selected_values
                )


                issues_provider.addFeature(
                    issue_feature
                )


                record = {}


                for field_name in report_fields:

                    record[
                        field_name
                    ] = feature[
                        field_name
                    ]


                record.update({

                    'QA_STATUS':
                        status,

                    'QA_ISSUE':
                        issue,

                    'QA_ACTION':
                        action,

                    'DUPLICATE_WITH':
                        duplicate_with,

                    'DUP_DISTANCE_M':
                        duplicate_distance,

                    'ORIGINAL_X':
                        original_x,

                    'ORIGINAL_Y':
                        original_y,

                    'CORRECTED_X':
                        corrected_x,

                    'CORRECTED_Y':
                        corrected_y
                })


                issue_records.append(
                    record
                )


        # =====================================================
        # EXPORT EXCEL
        # =====================================================

        processing.run(
            'native:exporttospreadsheet',
            {
                'LAYERS': [
                    issues_layer
                ],

                'USE_ALIAS':
                    False,

                'FORMATTED_VALUES':
                    False,

                'OUTPUT':
                    excel_path,

                'OVERWRITE':
                    True
            },
            context=context,
            feedback=feedback
        )


        # =====================================================
        # PDF COUNTS
        # =====================================================

        error_total = (
            missing_count
            + outside_count
            + invalid_count
        )


        warning_total = (
            duplicate_count
        )


        fixed_total = (
            swapped_count
        )


        report_date = (
            QDateTime
            .currentDateTime()
            .toString(
                'dd MMM yyyy - hh:mm'
            )
        )


        # =====================================================
        # CLEAN VALUES FOR PDF
        # =====================================================

        def clean(value):

            if value is None:
                return ''


            try:

                if QgsVariantUtils.isNull(
                    value
                ):

                    return ''

            except Exception:

                pass


            if isinstance(
                value,
                float
            ):

                return (
                    f'{value:.3f}'
                    if abs(value) < 100
                    else
                    f'{value:.6f}'
                )


            return html.escape(
                str(value)
            )


        # =====================================================
        # PDF HEADERS
        # =====================================================

        details_headers = ''


        for field_name in report_fields:

            details_headers += (
                '<th>'
                + clean(
                    field_name
                )
                + '</th>'
            )


        qa_pdf_fields = [

            ('QA_STATUS', 'Status'),

            ('QA_ISSUE', 'Issue'),

            ('QA_ACTION', 'Action'),

            (
                'DUPLICATE_WITH',
                'Duplicate With'
            ),

            (
                'DUP_DISTANCE_M',
                'Distance (m)'
            ),

            (
                'ORIGINAL_X',
                'Original X'
            ),

            (
                'ORIGINAL_Y',
                'Original Y'
            ),

            (
                'CORRECTED_X',
                'Corrected X'
            ),

            (
                'CORRECTED_Y',
                'Corrected Y'
            )
        ]


        for field_name, label in qa_pdf_fields:

            details_headers += (
                '<th>'
                + label
                + '</th>'
            )


        # =====================================================
        # PDF DETAIL ROWS
        # =====================================================

        issue_rows = ''


        for record in issue_records:

            status = record[
                'QA_STATUS'
            ]


            if status == 'ERROR':

                status_color = (
                    '#c62828'
                )

            elif status == 'WARNING':

                status_color = (
                    '#ef6c00'
                )

            elif status == 'FIXED':

                status_color = (
                    '#1565c0'
                )

            else:

                status_color = (
                    '#455a64'
                )


            issue_rows += '<tr>'


            # Selected source fields
            for field_name in report_fields:

                issue_rows += (
                    '<td>'
                    + clean(
                        record.get(
                            field_name,
                            ''
                        )
                    )
                    + '</td>'
                )


            # Status
            issue_rows += f"""
            <td style="
                color:{status_color};
                font-weight:bold;
                white-space:nowrap;
            ">
                {clean(status)}
            </td>
            """


            # Issue
            issue_rows += (
                '<td>'
                + clean(
                    record[
                        'QA_ISSUE'
                    ]
                )
                + '</td>'
            )


            # Action
            issue_rows += (
                '<td>'
                + clean(
                    record[
                        'QA_ACTION'
                    ]
                )
                + '</td>'
            )


            # Duplicate With
            issue_rows += (
                '<td>'
                + clean(
                    record[
                        'DUPLICATE_WITH'
                    ]
                )
                + '</td>'
            )


            # Distance
            distance_value = record[
                'DUP_DISTANCE_M'
            ]


            if distance_value is not None:

                distance_text = (
                    f'{distance_value:.2f}'
                )

            else:

                distance_text = ''


            issue_rows += (
                '<td>'
                + distance_text
                + '</td>'
            )


            # Original X/Y
            issue_rows += (
                '<td>'
                + clean(
                    record[
                        'ORIGINAL_X'
                    ]
                )
                + '</td>'
            )


            issue_rows += (
                '<td>'
                + clean(
                    record[
                        'ORIGINAL_Y'
                    ]
                )
                + '</td>'
            )


            # Corrected X/Y
            issue_rows += (
                '<td>'
                + clean(
                    record[
                        'CORRECTED_X'
                    ]
                )
                + '</td>'
            )


            issue_rows += (
                '<td>'
                + clean(
                    record[
                        'CORRECTED_Y'
                    ]
                )
                + '</td>'
            )


            issue_rows += '</tr>'


        # =====================================================
        # PDF HTML
        # =====================================================

        report_html = f"""
        <html>

        <head>

        <style>

        body {{
            font-family: Arial;
            background-color: #f4f7fa;
            color: #263238;
            margin: 0;
        }}


        .header {{
            background-color: #23475b;
            color: white;
            padding: 24px;
        }}


        .header h1 {{
            margin: 0;
            font-size: 26px;
        }}


        .header p {{
            color: #d9e5eb;
            font-size: 11px;
        }}


        .section {{
            margin: 22px 28px;
        }}


        .section-title {{
            color: #23475b;
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
        }}


        .cards {{
            width: 100%;
            border-spacing: 6px;
        }}


        .card {{
            background-color: white;
            border: 1px solid #dfe6eb;
            padding: 12px;
            text-align: center;
        }}


        .number {{
            font-size: 23px;
            font-weight: bold;
        }}


        .label {{
            color: #607d8b;
            font-size: 10px;
        }}


        .pass {{
            color: #2e7d32;
        }}


        .error {{
            color: #c62828;
        }}


        .warning {{
            color: #ef6c00;
        }}


        .fixed {{
            color: #1565c0;
        }}


        table.summary {{
            width: 100%;
            border-collapse: collapse;
            background-color: white;
            font-size: 9px;
        }}


        table.summary th {{
            background-color: #e7eef2;
            color: #23475b;
            border: 1px solid #c8d1d6;
            padding: 5px;
            text-align: left;
            white-space: nowrap;
        }}


        table.summary td {{
            border: 1px solid #d0d7dc;
            padding: 5px;
            vertical-align: top;
        }}


        .details {{
            font-size: 7px;
        }}


        .details th {{
            font-size: 7px;
        }}


        .details td {{
            font-size: 7px;
        }}


        .small {{
            font-size: 10px;
            color: #607d8b;
        }}


        .footer {{
            margin: 28px;
            padding-top: 8px;
            border-top: 1px solid #cfd8dc;
            font-size: 8px;
            color: #78909c;
        }}

        </style>

        </head>


        <body>


        <!-- PAGE 1 -->

        <div class="header">

            <h1>
                Spatial Data QA/QC Report
            </h1>

            <p>

                Automated Spatial Data
                Quality Control

                <br>

                Generated:
                {report_date}

                <br>

                Duplicate tolerance:
                {duplicate_tolerance:.2f} m

            </p>

        </div>


        <div class="section">

            <div class="section-title">
                Dataset Overview
            </div>


            <table class="cards">

                <tr>


                    <td class="card">

                        <div class="number">
                            {total_count}
                        </div>

                        <div class="label">
                            Total Records
                        </div>

                    </td>


                    <td class="card">

                        <div class="number pass">
                            {pass_count}
                        </div>

                        <div class="label">
                            Passed
                        </div>

                    </td>


                    <td class="card">

                        <div class="number error">
                            {error_total}
                        </div>

                        <div class="label">
                            Errors
                        </div>

                    </td>


                    <td class="card">

                        <div class="number warning">
                            {warning_total}
                        </div>

                        <div class="label">
                            Warnings
                        </div>

                    </td>


                    <td class="card">

                        <div class="number fixed">
                            {fixed_total}
                        </div>

                        <div class="label">
                            Auto Fixed
                        </div>

                    </td>


                </tr>

            </table>

        </div>


        <div class="section">

            <div class="section-title">
                Issue Summary
            </div>


            <table class="summary">

                <tr>

                    <th>Issue Type</th>

                    <th>Count</th>

                    <th>Recommended Action</th>

                </tr>


                <tr>

                    <td>
                        Missing Coordinates
                    </td>

                    <td>
                        {missing_count}
                    </td>

                    <td>
                        Manual Review
                    </td>

                </tr>


                <tr>

                    <td>
                        Potential Duplicates
                    </td>

                    <td>
                        {duplicate_count}
                    </td>

                    <td>
                        Verify asset or location
                    </td>

                </tr>


                <tr>

                    <td>
                        X / Y Swapped
                    </td>

                    <td>
                        {swapped_count}
                    </td>

                    <td>
                        Automatically Corrected
                    </td>

                </tr>


                <tr>

                    <td>
                        Outside Valid Extent
                    </td>

                    <td>
                        {outside_count}
                    </td>

                    <td>
                        Manual Review
                    </td>

                </tr>


                <tr>

                    <td>
                        Invalid Coordinate Values
                    </td>

                    <td>
                        {invalid_count}
                    </td>

                    <td>
                        Manual Review
                    </td>

                </tr>

            </table>

        </div>


        <div class="section">

            <div class="section-title">
                QA/QC Method
            </div>


            <p class="small">

                This report was generated automatically
                using a PyQGIS spatial data quality-control
                workflow.

                Records were checked for missing coordinates,
                invalid coordinate values, locations outside
                the valid project extent, potential X/Y
                coordinate swaps, and duplicate locations.

                Duplicate detection was performed using a
                distance tolerance of
                {duplicate_tolerance:.2f} meters.

                X/Y values were automatically corrected only
                when the original coordinate pair was outside
                the valid project extent and the swapped
                coordinate pair fell inside the valid extent.

            </p>

        </div>


        <div class="footer">

            Spatial QA/QC Automation Tool

            <br>

            Generated using QGIS and PyQGIS

        </div>


        <!-- DETAIL PAGE -->

        <div style="
            page-break-before: always;
        ">
        </div>


        <div class="section">

            <div class="section-title">
                Issue Details
            </div>


            <p class="small">

                Records requiring manual review or
                automatically corrected by the QA/QC
                workflow.

            </p>


            <table class="summary details">

                <tr>

                    {details_headers}

                </tr>


                {issue_rows}


            </table>

        </div>


        <div class="footer">

            Spatial QA/QC Automation Tool

            <br>

            Issue Details

        </div>


        </body>

        </html>
        """


        # =====================================================
        # CREATE LANDSCAPE PDF
        # =====================================================

        document = QTextDocument()

        document.setHtml(
            report_html
        )


        printer = QPrinter()

        printer.setOutputFormat(
            QPrinter.PdfFormat
        )


        printer.setOrientation(
            QPrinter.Landscape
        )


        printer.setOutputFileName(
            pdf_path
        )


        document.print_(
            printer
        )


        # =====================================================
        # COMPLETE
        # =====================================================

        feedback.pushInfo(
            'QA/QC completed successfully.'
        )


        feedback.pushInfo(
            'Total Records: '
            + str(total_count)
        )


        feedback.pushInfo(
            'Passed: '
            + str(pass_count)
        )


        feedback.pushInfo(
            'Potential Duplicates: '
            + str(duplicate_count)
        )


        feedback.pushInfo(
            'X/Y Swaps Corrected: '
            + str(swapped_count)
        )


        feedback.pushInfo(
            'Issues Excel: '
            + excel_path
        )


        feedback.pushInfo(
            'PDF Report: '
            + pdf_path
        )


        return {

            self.OUTPUT:
                dest_id,

            self.EXCEL:
                excel_path,

            self.PDF:
                pdf_path
        }