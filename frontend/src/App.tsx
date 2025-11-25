import { useCallback, useEffect, useRef, useState } from 'react'
import {
  Card,
  Empty,
  Layout,
  List,
  Select,
  Space,
  Statistic,
  Tabs,
  Tag,
  Typography,
  Upload,
  message,
} from 'antd'
import type { UploadProps } from 'antd'
import type { UploadRequestOption } from 'rc-upload/lib/interface'
import { InboxOutlined } from '@ant-design/icons'

import './App.css'
import { apiClient } from './api/client'
import type { ResultResponse } from './types/api'

const { Header, Content } = Layout
const { Title, Paragraph, Text } = Typography

type PipelineStatus = 'idle' | 'uploading' | 'polling' | 'success' | 'error'

function App() {
  const [status, setStatus] = useState<PipelineStatus>('idle')
  const [requestId, setRequestId] = useState<string | null>(null)
  const [result, setResult] = useState<ResultResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const pollingRef = useRef<number | null>(null)
  const [messageApi, contextHolder] = message.useMessage()

  const clearPolling = () => {
    if (pollingRef.current) {
      window.clearInterval(pollingRef.current)
      pollingRef.current = null
    }
  }

  const startPolling = useCallback((reqId: string) => {
    setStatus('polling')
    setError(null)
    setResult(null)
    let attempts = 0
    const maxAttempts = 10

    const fetchResult = async () => {
      attempts += 1
      try {
        const { data } = await apiClient.get<ResultResponse>(
          `/api/v1/result/${reqId}`,
        )
        setResult(data)
        setStatus('success')
        clearPolling()
        messageApi.success('识别完成')
      } catch (err: unknown) {
        if (
          typeof err === 'object' &&
          err !== null &&
          'response' in err &&
          (err as any).response?.status === 404
        ) {
          if (attempts >= maxAttempts) {
            setStatus('error')
            setError('识别超时，请重试或重新拍摄')
            clearPolling()
          }
          return
        }
        setStatus('error')
        setError('识别失败，请稍后再试')
        clearPolling()
      }
    }

    fetchResult()
    pollingRef.current = window.setInterval(fetchResult, 1500)
  }, [messageApi])

  const [bookSize, setBookSize] = useState<string>('16k')
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)

  useEffect(() => () => clearPolling(), [])

  // Cleanup preview URL on unmount or change
  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl)
      }
    }
  }, [previewUrl])

  const handleUpload = async (options: UploadRequestOption) => {
    const file = options.file as File
    // Create preview URL
    const objectUrl = URL.createObjectURL(file)
    setPreviewUrl(objectUrl)

    setStatus('uploading')
    setError(null)
    setResult(null)
    const formData = new FormData()
    formData.append('file', file)
    formData.append('book_size', bookSize)

    try {
      const { data } = await apiClient.post('/api/v1/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setRequestId(data.request_id)
      messageApi.loading('开始识别...', 1)
      startPolling(data.request_id)
      options.onSuccess?.(data, file)
    } catch (err) {
      setStatus('error')
      const detail = (err as any)?.response?.data?.detail ?? '上传失败'
      setError(detail)
      messageApi.error(detail)
      options.onError?.(err as Error)
    }
  }

  const uploadProps: UploadProps = {
    name: 'file',
    multiple: false,
    showUploadList: false,
    accept: '.jpg,.jpeg,.png',
    customRequest: handleUpload,
  }

  const statusTagMap: Record<PipelineStatus, { color: string; text: string }> = {
    idle: { color: 'default', text: '待上传' },
    uploading: { color: 'processing', text: '上传中' },
    polling: { color: 'warning', text: '识别中' },
    success: { color: 'success', text: '识别完成' },
    error: { color: 'error', text: '识别失败' },
  }

  const renderTexts = () => {
    if (!result) return <Empty description="暂无识别结果" />
    return (
      <List
        dataSource={result.texts}
        renderItem={(item) => (
          <List.Item>
            <Space direction="vertical">
              <Text>{item.content}</Text>
              <Space wrap>
                {item.formatted_typography ? (
                  <Tag color="purple">{item.formatted_typography}</Tag>
                ) : (
                  item.font && <Tag color="blue">{item.font}</Tag>
                )}
                <Text type="secondary">
                  置信度 {(item.confidence * 100).toFixed(1)}%
                </Text>
                {item.font_confidence !== undefined && (
                  <Text type="secondary">
                    字体可信度 {(item.font_confidence * 100).toFixed(1)}%
                  </Text>
                )}
              </Space>
            </Space>
          </List.Item>
        )}
      />
    )
  }

  const renderFontsSummary = () => {
    if (!result || result.fonts_summary.length === 0) {
      return <Empty description="暂无字体统计" />
    }
    return (
      <List
        dataSource={result.fonts_summary}
        renderItem={(item) => (
          <List.Item>
            <Space direction="vertical">
              <Text strong>{item.font}</Text>
              <Text type="secondary">出现 {item.occurrences} 次</Text>
              <Text type="secondary">
                平均可信度 {(item.avg_confidence * 100).toFixed(1)}%
              </Text>
            </Space>
          </List.Item>
        )}
      />
    )
  }

  return (
    <Layout className="layout">
      {contextHolder}
      <Header className="header">
        <Title level={3}>CoverOCR · 封面识别</Title>
        <Paragraph>上传一本教材封面，系统自动识别书籍、文字、字体。</Paragraph>
      </Header>
      <Content className="content">
        <div className="grid">
          <Card title="上传封面" bordered={false}>
            <div style={{ marginBottom: 16 }}>
              <Text strong>选择书本尺寸：</Text>
              <Select
                value={bookSize}
                onChange={setBookSize}
                style={{ width: 200, marginLeft: 8 }}
                options={[
                  { value: '16k', label: '16开 (教材/参考书)' },
                  { value: 'a4', label: 'A4 (打印纸/大开本)' },
                  { value: '32k', label: '32开 (小册子/小说)' },
                ]}
              />
            </div>
            <Upload.Dragger {...uploadProps} disabled={status === 'uploading'}>
              {previewUrl ? (
                <div style={{ padding: '20px 0' }}>
                  <img
                    src={previewUrl}
                    alt="Cover Preview"
                    style={{
                      maxWidth: '100%',
                      maxHeight: '300px',
                      objectFit: 'contain',
                      borderRadius: '8px',
                      boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                    }}
                  />
                  <p className="upload-text" style={{ marginTop: 10 }}>
                    点击更换图片
                  </p>
                </div>
              ) : (
                <>
                  <p className="upload-icon">
                    <InboxOutlined />
                  </p>
                  <p className="upload-text">点击或拖拽 JPG / PNG 图片到此处</p>
                  <p className="upload-hint">建议使用实拍封面，大小不超过 20MB</p>
                </>
              )}
            </Upload.Dragger>
            <Space className="status-row">
              <Text>流程状态</Text>
              <Tag color={statusTagMap[status].color}>
                {statusTagMap[status].text}
              </Tag>
              {requestId && (
                <Text type="secondary" copyable>
                  请求 ID: {requestId}
                </Text>
              )}
            </Space>
            {error && <Text type="danger">{error}</Text>}
          </Card>
          <Card
            title="识别结果"
            bordered={false}
            extra={
              result ? (
                <Statistic
                  title="耗时"
                  value={result.elapsed_ms / 1000}
                  precision={2}
                  suffix="s"
                />
              ) : null
            }
          >
            <Tabs
              items={[
                { key: 'text', label: '文字识别', children: renderTexts() },
                { key: 'font', label: '字体统计', children: renderFontsSummary() },
              ]}
            />
          </Card>
        </div>
      </Content>
    </Layout>
  )
}

export default App
