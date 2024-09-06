import { H5 } from '../../../AbstractElements';
import { Javadata } from './Data';
import React, { Fragment } from 'react';
import { Card, CardBody, CardHeader, Col } from 'reactstrap';
import AceEditor from 'react-ace';
import 'ace-builds/src-noconflict/mode-java';
import 'ace-builds/src-noconflict/theme-monokai';
import 'ace-builds/src-noconflict/ext-language_tools';

const JavascriptMode = () => {
    return (
        <Fragment>
            <Col xl="6">
                <Card>
                    <CardHeader>
                        <H5>Javascript Mode</H5>
                    </CardHeader>
                    <CardBody>
                        <AceEditor
                            style={{ marginTop: '0px', width: '663px', height: '428px', marginLeft: '0px' }}
                            mode="javascript"
                            theme="monokai"
                            value={Javadata}
                            name="blah2"
                            setOptions={{ useWorker: false }}
                            fontSize={14}
                            showPrintMargin={true}
                            showGutter={true}
                            editorProps={{ $blockScrolling: true }}
                            highlightActiveLine={true} />
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    );
};
export default JavascriptMode;