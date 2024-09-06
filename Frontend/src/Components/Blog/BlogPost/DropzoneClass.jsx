import React, { Fragment } from 'react';
import Dropzone from 'react-dropzone-uploader';
import { Form } from 'reactstrap';

const DropzoneClass = () => {
    const getUploadParams = ({ meta }) => {
        return { url: 'https://httpbin.org/post' };
    };
    const handleChangeStatus = ({ meta, file }, status) => { };

    return (
        <Fragment>
            <Form className="m-b-20">
                <div className="m-0 dz-message needsclick">
                    <Dropzone
                        getUploadParams={getUploadParams}
                        onChangeStatus={handleChangeStatus}
                        maxFiles={1}
                        multiple={false}
                        canCancel={false}
                        inputContent="Drop files here or click to upload."
                        styles={{
                            dropzone: { width: '100%', height: 50 },
                            dropzoneActive: { borderColor: 'green' },
                        }}
                    />
                </div>
            </Form>
        </Fragment>
    );
};

export default DropzoneClass;