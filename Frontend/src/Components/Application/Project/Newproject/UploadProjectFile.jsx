import React, { Fragment } from 'react';
import { Col, FormGroup, Label, Row } from 'reactstrap';
import { UploadProjectFile } from '../../../../Constant';
import Dropzone from 'react-dropzone-uploader';

const UploadProjectFileClass = () => {
  const getUploadParams = ({ meta }) => {
    return {
      url: 'https://httpbin.org/post',
    };
  };

  // called every time a file's `status` changes
  const handleChangeStatus = ({ meta, file }, status) => {};

  return (
    <Fragment>
      <Row>
        <Col>
          <FormGroup>
            <Label>{UploadProjectFile}</Label>
            <Dropzone
              className='dropzone dz-clickable'
              getUploadParams={getUploadParams}
              onChangeStatus={handleChangeStatus}
              maxFiles={1}
              multiple={false}
              canCancel={false}
              inputContent='Drop A File'
              styles={{
                dropzone: { width: '100%', height: 150 },
                dropzoneActive: { borderColor: 'green' },
              }}
            />
          </FormGroup>
        </Col>
      </Row>
    </Fragment>
  );
};

export default UploadProjectFileClass;
