import os
import logging
import requests
import json
import re
from typing import List, Dict, Any

class ActionItemExtractor:
    """Service for extracting action items from transcribed text"""
    
    def __init__(self):
        # Use OpenAI GPT API for action item extraction
        self.api_key = os.environ.get('OPENAI_API_KEY', 'your-openai-api-key')
        self.api_url = 'https://api.openai.com/v1/chat/completions'
    
    def extract_action_items(self, text: str, language: str = 'en') -> List[Dict[str, Any]]:
        """
        Extract action items from transcribed text
        
        Args:
            text: Transcribed text from meeting
            language: Language of the text
            
        Returns:
            List of action items with details
        """
        try:
            # Create language-specific prompts
            prompts = {
                'en': self._get_english_prompt(),
                'es': self._get_spanish_prompt(),
                'fr': self._get_french_prompt(),
                'de': self._get_german_prompt(),
                'it': self._get_italian_prompt(),
                'pt': self._get_portuguese_prompt(),
            }
            
            # Use English prompt as fallback
            prompt = prompts.get(language, prompts['en'])
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': 'gpt-3.5-turbo',
                'messages': [
                    {
                        'role': 'system',
                        'content': prompt
                    },
                    {
                        'role': 'user',
                        'content': f"Please analyze this meeting transcript and extract action items:\n\n{text}"
                    }
                ],
                'temperature': 0.3,
                'max_tokens': 1500
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # Parse the response to extract structured action items
                action_items = self._parse_action_items(content, language)
                return action_items
            else:
                logging.error(f"Action item extraction API error: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logging.error(f"Action item extraction error: {str(e)}")
            return []
    
    def _get_english_prompt(self) -> str:
        """Get English language prompt for action item extraction"""
        return """You are an AI assistant specialized in analyzing meeting transcripts to identify action items. 

Your task is to:
1. Identify clear action items, tasks, or commitments mentioned in the transcript
2. Extract who is responsible (if mentioned)
3. Identify any deadlines or timeframes
4. Determine the priority level (High, Medium, Low)
5. Provide a brief description of each action item

Format your response as a JSON array with objects containing:
- "task": Brief description of the action item
- "assignee": Person responsible (or "Not specified" if unclear)
- "deadline": Deadline or timeframe (or "Not specified" if unclear)
- "priority": Priority level (High/Medium/Low)
- "context": Brief context from the meeting

Only include clear, actionable items. Ignore general discussion points that don't result in specific actions."""

    def _get_spanish_prompt(self) -> str:
        """Get Spanish language prompt"""
        return """Eres un asistente de IA especializado en analizar transcripciones de reuniones para identificar elementos de acción.

Tu tarea es:
1. Identificar elementos de acción claros, tareas o compromisos mencionados en la transcripción
2. Extraer quién es responsable (si se menciona)
3. Identificar plazos o marcos temporales
4. Determinar el nivel de prioridad (Alta, Media, Baja)
5. Proporcionar una breve descripción de cada elemento de acción

Formatea tu respuesta como un array JSON con objetos que contengan:
- "task": Breve descripción del elemento de acción
- "assignee": Persona responsable (o "No especificado" si no está claro)
- "deadline": Plazo o marco temporal (o "No especificado" si no está claro)
- "priority": Nivel de prioridad (Alta/Media/Baja)
- "context": Breve contexto de la reunión

Solo incluye elementos claros y accionables. Ignora puntos de discusión general que no resulten en acciones específicas."""

    def _get_french_prompt(self) -> str:
        """Get French language prompt"""
        return """Vous êtes un assistant IA spécialisé dans l'analyse de transcriptions de réunions pour identifier les éléments d'action.

Votre tâche est de :
1. Identifier les éléments d'action clairs, les tâches ou les engagements mentionnés dans la transcription
2. Extraire qui est responsable (si mentionné)
3. Identifier les échéances ou les délais
4. Déterminer le niveau de priorité (Élevé, Moyen, Faible)
5. Fournir une brève description de chaque élément d'action

Formatez votre réponse comme un tableau JSON avec des objets contenant :
- "task": Brève description de l'élément d'action
- "assignee": Personne responsable (ou "Non spécifié" si peu clair)
- "deadline": Échéance ou délai (ou "Non spécifié" si peu clair)
- "priority": Niveau de priorité (Élevé/Moyen/Faible)
- "context": Bref contexte de la réunion

N'incluez que des éléments clairs et exploitables. Ignorez les points de discussion généraux qui ne résultent pas en actions spécifiques."""

    def _get_german_prompt(self) -> str:
        """Get German language prompt"""
        return """Sie sind ein KI-Assistent, der auf die Analyse von Besprechungsprotokollen spezialisiert ist, um Aktionselemente zu identifizieren.

Ihre Aufgabe ist es:
1. Klare Aktionselemente, Aufgaben oder Verpflichtungen im Protokoll zu identifizieren
2. Verantwortliche zu extrahieren (falls erwähnt)
3. Fristen oder Zeitrahmen zu identifizieren
4. Prioritätsstufe zu bestimmen (Hoch, Mittel, Niedrig)
5. Eine kurze Beschreibung jedes Aktionselements zu liefern

Formatieren Sie Ihre Antwort als JSON-Array mit Objekten, die enthalten:
- "task": Kurze Beschreibung des Aktionselements
- "assignee": Verantwortliche Person (oder "Nicht spezifiziert" falls unklar)
- "deadline": Frist oder Zeitrahmen (oder "Nicht spezifiziert" falls unklar)
- "priority": Prioritätsstufe (Hoch/Mittel/Niedrig)
- "context": Kurzer Kontext aus der Besprechung

Nur klare, umsetzbare Elemente einschließen. Allgemeine Diskussionspunkte ignorieren, die nicht zu spezifischen Aktionen führen."""

    def _get_italian_prompt(self) -> str:
        """Get Italian language prompt"""
        return """Sei un assistente IA specializzato nell'analisi di trascrizioni di riunioni per identificare elementi d'azione.

Il tuo compito è:
1. Identificare elementi d'azione chiari, compiti o impegni menzionati nella trascrizione
2. Estrarre chi è responsabile (se menzionato)
3. Identificare scadenze o tempistiche
4. Determinare il livello di priorità (Alto, Medio, Basso)
5. Fornire una breve descrizione di ogni elemento d'azione

Formatta la tua risposta come array JSON con oggetti contenenti:
- "task": Breve descrizione dell'elemento d'azione
- "assignee": Persona responsabile (o "Non specificato" se poco chiaro)
- "deadline": Scadenza o tempistica (o "Non specificato" se poco chiaro)
- "priority": Livello di priorità (Alto/Medio/Basso)
- "context": Breve contesto dalla riunione

Includi solo elementi chiari e azionabili. Ignora punti di discussione generale che non risultano in azioni specifiche."""

    def _get_portuguese_prompt(self) -> str:
        """Get Portuguese language prompt"""
        return """Você é um assistente de IA especializado em analisar transcrições de reuniões para identificar itens de ação.

Sua tarefa é:
1. Identificar itens de ação claros, tarefas ou compromissos mencionados na transcrição
2. Extrair quem é responsável (se mencionado)
3. Identificar prazos ou cronogramas
4. Determinar o nível de prioridade (Alto, Médio, Baixo)
5. Fornecer uma breve descrição de cada item de ação

Formate sua resposta como um array JSON com objetos contendo:
- "task": Breve descrição do item de ação
- "assignee": Pessoa responsável (ou "Não especificado" se não estiver claro)
- "deadline": Prazo ou cronograma (ou "Não especificado" se não estiver claro)
- "priority": Nível de prioridade (Alto/Médio/Baixo)
- "context": Breve contexto da reunião

Inclua apenas itens claros e acionáveis. Ignore pontos de discussão geral que não resultem em ações específicas."""

    def _parse_action_items(self, content: str, language: str) -> List[Dict[str, Any]]:
        """Parse the GPT response to extract structured action items"""
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                action_items = json.loads(json_str)
                
                # Validate and clean up the action items
                cleaned_items = []
                for item in action_items:
                    if isinstance(item, dict) and 'task' in item:
                        cleaned_item = {
                            'task': item.get('task', 'Unknown task'),
                            'assignee': item.get('assignee', 'Not specified'),
                            'deadline': item.get('deadline', 'Not specified'),
                            'priority': item.get('priority', 'Medium'),
                            'context': item.get('context', 'No context provided')
                        }
                        cleaned_items.append(cleaned_item)
                
                return cleaned_items
            else:
                # Fallback: try to parse line by line
                return self._parse_fallback(content, language)
                
        except json.JSONDecodeError:
            logging.warning("Failed to parse JSON response, using fallback parser")
            return self._parse_fallback(content, language)
        except Exception as e:
            logging.error(f"Error parsing action items: {str(e)}")
            return []
    
    def _parse_fallback(self, content: str, language: str) -> List[Dict[str, Any]]:
        """Fallback parser for non-JSON responses"""
        action_items = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('•') or line.startswith('*')):
                # Extract basic action item
                task = line.lstrip('-•* ').strip()
                if task:
                    action_items.append({
                        'task': task,
                        'assignee': 'Not specified',
                        'deadline': 'Not specified',
                        'priority': 'Medium',
                        'context': 'Extracted from meeting transcript'
                    })
        
        return action_items
