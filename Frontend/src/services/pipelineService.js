import { pipeline } from '../data/mockPipeline.js'
import { simulateRequest } from './simulateRequest.js'

export const getPipelineStatus = () => simulateRequest(pipeline)
